/*
This file contains the main/callbacks needed for the application.
MIT License - 2019 - Charles Machalow
*/

#include <chrono>
#include <iostream>
#include <string>

#ifdef _WIN32
#include "client/windows/crash_generation/client_info.h"
#include "client/windows/crash_generation/crash_generation_server.h"
#else
#error Implementation missing for OS
#endif

#include "../../local/CLI11.hpp"
#include "Logging.h"
#include "PdaCrashContext.h"
#include "Process.h"
#include "Utility.h"

static void ShowClientConnected(void* context, const google_breakpad::ClientInfo* client_info)
{
	LOG("Client with pid " + std::to_string(client_info->pid()) + " connected");
}

static void ShowClientCrashed(void* context, const google_breakpad::ClientInfo* client_info, const std::wstring* dump_path)
{
	LOG("Client with pid " + std::to_string(client_info->pid()) + " has crashed");

	if (context)
	{
		pda::PdaCrashContext* crashContext = reinterpret_cast<pda::PdaCrashContext*>(context);
		if (dump_path)
		{
			crashContext->setCrashDumpFilePath(*dump_path);
		}
		else
		{
			LOG("dump_path was NULL... that should not happen!");
		}
		crashContext->report();
	}
	else
	{
		LOG("No context available! That should not happen!");
	}
}

static void ShowClientExited(void* context, const google_breakpad::ClientInfo* client_info)
{
	LOG("Client with pid " + std::to_string(client_info->pid()) + " exited");
}

int main(int argc, char* argv[])
{
	CLI::App app{ "PyDumpAnalyzer (PDA) Crash Reporting Server" };

	/* Required Params */
	std::string reportingServer;
	app.add_option("-r, --reporting_server", reportingServer, "The analysis server that will be used to report crashes to. Be sure to include http/https per what the server supports.")->required();

	std::string application;
	app.add_option("-a, --application", application, "The application name to be reported to the server.")->required();

	/* Optional Params (General) */
	bool verbose = false;
	app.add_flag("-v, --verbose", verbose, "If given, be verbose and print some logging.");

	/* Optional Params (Reporting) */
	DWORD pidToMonitor = 0;
	app.add_option("-p, --pid", pidToMonitor, "pid for the process to monitor (if not given, will report immediately with just the given data)");

	std::string tag;
	app.add_option("-t, --tag", tag, "The tag to use for anything reported up to the analysis server");

	std::string applicationVersion;
	app.add_option("-n, --application_version", applicationVersion, "The version for the application we're reporting for");

	std::string symbolsFilePath;
	app.add_option("-y, --symbols", symbolsFilePath, "The path to a symbols file");

	std::string executableFilePath;
	app.add_option("-e, --executable", symbolsFilePath, "The path to an executable file");

	std::string crashDumpFilePath;
	app.add_option("-c, --crash_dump", crashDumpFilePath, "The path to an executable file");

	CLI11_PARSE(app, argc, argv);

	pda::setLogging(verbose);

	pda::PdaCrashContext pdaCrashContext(pda::toWString(reportingServer), pda::toWString(application));

	/* Set all parameters we've been given */

	if (tag.size())
	{
		pdaCrashContext.setTag(pda::toWString(tag));
	}

	if (applicationVersion.size())
	{
		pdaCrashContext.setApplicationVersion(pda::toWString(applicationVersion));
	}

	if (symbolsFilePath.size())
	{
		pdaCrashContext.setSymbolsFilePath(pda::toWString(symbolsFilePath));
	}

	if (executableFilePath.size())
	{
		pdaCrashContext.setExecutableFilePath(pda::toWString(executableFilePath));
	}

	if (crashDumpFilePath.size())
	{
		pdaCrashContext.setCrashDumpFilePath(pda::toWString(crashDumpFilePath));
	}

	if (pidToMonitor)
	{
		std::wstring dumpPath = L".";
		// pid was given, so monitor it
		std::unique_ptr<google_breakpad::CrashGenerationServer> crashGenerationServer(
			new google_breakpad::CrashGenerationServer(
				pda::getNamedPipeForPid(pidToMonitor),
				NULL,
				ShowClientConnected,
				&pdaCrashContext,
				ShowClientCrashed,
				&pdaCrashContext,
				ShowClientExited,
				&pdaCrashContext,
				NULL,
				NULL,
				true,
				&dumpPath));

		if (!crashGenerationServer->Start())
		{
			LOG("Failed to start crash generation server");
			return EXIT_FAILURE;
		}

		pda::waitForProcessExit(pidToMonitor);
	}
	else
	{
		if (!pdaCrashContext.report())
		{
			LOG("Reporting failed");
			return EXIT_FAILURE;
		}
	}

	return EXIT_SUCCESS;
}