/*
WIP
*/

#include <chrono>
#include <iostream>
#include <stdlib.h>
#include <stdio.h>
#include <thread>

#include "client/windows/crash_generation/client_info.h"
#include "client/windows/crash_generation/crash_generation_server.h"
#include "common/windows/http_upload.h"

#include "../../local/CLI11.hpp"


using namespace google_breakpad;

static void ShowClientConnected(void* context, const ClientInfo* client_info)
{
	std::clog << "Client connected with a pid of: " << client_info->pid() << std::endl;
}

static void ShowClientCrashed(void* context, const ClientInfo* client_info, const wstring* dump_path)
{
	std::clog << "Client requested a dump with a pid of: " << client_info->pid() << std::endl;
	std::clog << "Attempting to send to server..." << std::endl;

	std::map<std::wstring, std::wstring> parameters;
	parameters[L"os"] = L"Windows";

	std::map<std::wstring, std::wstring> files;

	files[L"dump"] = *dump_path;
	int timeout_ms = 60 * 1000;
	int response_code = 0;
	std::wstring response_body;

	bool result = HTTPUpload::SendMultipartPostRequest(
		L"http://localhost:5000/add",
		parameters,
		files,
		&timeout_ms,
		&response_body,
		&response_code
	);
	std::cout << "Result: " << result << std::endl;

	std::wclog << response_code << std::endl << response_body << std::endl;

}

static void ShowClientExited(void* context, const ClientInfo* client_info)
{
	std::clog << "Client exited with a pid of: " << client_info->pid() << std::endl;
}

bool isProcessRunning(HANDLE process)
{
	DWORD exitCode = 0;
	bool success = GetExitCodeProcess(process, &exitCode);

	if (!success)
	{
		return false;
	}

	return exitCode == STILL_ACTIVE;
}

// todo: Pass context including reporting server/tag to callbacks.
// todo: ensure paths are relative (not refering to my dev system's paths)

int main(int argc, char* argv[])
{
	CLI::App app{ "PyDumpAnalyzer (PDA) Crash Reporting Server" };
	
	DWORD pid;
	app.add_option("-p, --pid", pid, "pid for the process to monitor")->required();
	
	std::string reportingServer;
	app.add_option("-r, --reporting_server", reportingServer, "The analysis server that will be used to report crashes to. Be sure to include http/https per what the server supports.")->required();

	std::string tag;
	app.add_option("-t, --tag", tag, "The tag to use for anything reported up to the analysis server");

	CLI11_PARSE(app, argc, argv);

	HANDLE handle = OpenProcess(PROCESS_QUERY_INFORMATION, false, pid);
	if (handle == NULL)
	{
		std::cerr << "Failed to get handle to pid: " << pid << std::endl;
		return EXIT_FAILURE;
	}
	else
	{
		std::clog << "Got a handle to pid: " << pid << std::endl;
	}

	// place dumps in the temp path
	TCHAR path[MAX_PATH + 1 /* null char */] = { 0 };
	DWORD length = GetTempPath(sizeof(path), path);
	std::wstring dumpPath(path, length);

	std::wstring pipeAsWStr = L"\\\\.\\pipe\\pda_pid\\" + std::to_wstring(pid);

	std::unique_ptr<CrashGenerationServer> crashGenerationServer(new CrashGenerationServer(pipeAsWStr,
		NULL,
		ShowClientConnected,
		NULL,
		ShowClientCrashed,
		NULL,
		ShowClientExited,
		NULL,
		NULL,
		NULL,
		true,
		&dumpPath));

	if (!crashGenerationServer->Start())
	{
		std::cerr << "Failed to start server" << std::endl;
		CloseHandle(handle);
		return EXIT_FAILURE;
	}

	DWORD secondsSlept = 1;
	while (isProcessRunning(handle))
	{
		std::this_thread::sleep_for(std::chrono::seconds(1));
		std::cout << secondsSlept << ") Slept a second" << std::endl;
		secondsSlept += 1;
	}

	std::cout << "Pid " << pid << " appears to be no longer running. Exiting." << std::endl;

	CloseHandle(handle);
	return EXIT_SUCCESS;
}