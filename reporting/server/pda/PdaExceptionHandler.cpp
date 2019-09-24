/*
This file contains the implementations for pda exception handling
MIT License - 2019 - Charles Machalow
*/

#ifdef _WIN32
#include "client/windows/handler/exception_handler.h"
#else
#error Implementation missing for OS
#endif

#include <iostream>

#include "Logging.h"
#include "PdaExceptionHandler.h"
#include "Process.h"
#include "Utility.h"

namespace pda
{
	PdaExceptionHandler::PdaExceptionHandler(const std::wstring exeLocation, const std::shared_ptr<pda::PdaCrashContext>& pdaCrashContext)
	{
		ExeLocation = exeLocation;
		PdaCrashContext = pdaCrashContext;
		AdditionalArgs = L"";

#ifdef _WIN32
		ExeProcessHandle = INVALID_HANDLE_VALUE;
#else
#error Implementation missing for OS
#endif
	}

	PdaExceptionHandler::~PdaExceptionHandler()
	{
		stopHandler();
	}

	bool PdaExceptionHandler::startHandler()
	{
		if (handlerIsStarted())
		{
			return true;
		}

		std::wstring args = L"\"" + ExeLocation + L"\" " + std::wstring(L"--reporting_server \"") + *PdaCrashContext->getReportingServer() +
			std::wstring(L"\" --application \"") + *PdaCrashContext->getApplicationName() + L"\""; 

		args += L" --pid " + std::to_wstring(GetCurrentProcessId());

		auto applicationVersion = PdaCrashContext->getApplicationVersion();
		if (applicationVersion)
		{
			args += L" --application_version \"" + *applicationVersion + L"\"";
		}
		auto tag = PdaCrashContext->getTag();

		if (tag)
		{
			args += L" --tag \"" + *tag + L"\"";
		}

#if _DEBUG
		args += L" --verbose";
#endif

		if (AdditionalArgs.size())
		{
			args += L" " + AdditionalArgs;
		}

		// technically i may be able to add --executable here.

#ifdef _WIN32
		STARTUPINFO startupInfo = { 0 };
		startupInfo.cb = sizeof(STARTUPINFO);
		PROCESS_INFORMATION processInfo = { 0 };
		if (!CreateProcess(NULL,
			(LPWSTR)args.c_str(),
			NULL,
			NULL,
			false,
			0 /*CREATE_NO_WINDOW*/,
			NULL,
			NULL,
			&startupInfo,
			&processInfo))
		{
			LOG("Failed to CreateProcess... Error: " + std::to_string(GetLastError()));
			return false;
		}

		ExeProcessHandle = processInfo.hProcess;

		auto pipe = pda::getNamedPipeForPid(GetCurrentProcessId());

		// Once the child opens creates the pipe, its ready for us. If somehow it doesn't open after 3 seconds, give up
		if (!pda::waitTillFileExists(pipe, std::chrono::seconds(3)))
		{
			LOG("Failed to find opened pipe by child process");
			stopHandler();
			return false;
		}

		ExceptionHandler = std::unique_ptr<google_breakpad::ExceptionHandler>(
			new google_breakpad::ExceptionHandler(
			L".", /* Ensure this is set to something! Otherwise dumps won't write! */
			NULL,
			NULL,
			NULL,
			google_breakpad::ExceptionHandler::HANDLER_ALL,
			MiniDumpNormal,
			pipe.c_str(),
			NULL));

		return true;

#else
#error Implementation missing for OS
#endif
	}

	bool PdaExceptionHandler::stopHandler()
	{
		if (!handlerIsStarted())
		{
			return true;
		}

#ifdef _WIN32
		if (!TerminateProcess(ExeProcessHandle, PROCESS_TERMINATE))
		{
			LOG("Failed to terminate... Error: " + std::to_string(GetLastError()));
			return false;
		}

		CloseHandle(ExeProcessHandle);
		ExeProcessHandle = NULL;
		ExceptionHandler = NULL;
#else
#error Implementation missing for OS
#endif

		return true;
	}

	bool PdaExceptionHandler::handlerIsStarted() const
	{
		bool started = false;
#ifdef _WIN32
		if (ExeProcessHandle != INVALID_HANDLE_VALUE)
		{
			started = true;
		}
#else
#error Implementation missing for OS
#endif
		return started;
	}

	void PdaExceptionHandler::setAdditionalArgs(const std::wstring extra)
	{
		AdditionalArgs = extra;
	}
};

