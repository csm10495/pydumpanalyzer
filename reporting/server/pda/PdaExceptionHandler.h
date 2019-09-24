/*
This file contains the headers for pda exception handling
MIT License - 2019 - Charles Machalow
*/

#pragma once

#ifdef _WIN32
#include "client/windows/handler/exception_handler.h"
#include <Windows.h>
#endif

#include <memory>
#include <string>

#include "PdaCrashContext.h"

namespace pda
{
	//! The exception handler, will attempt to have out of process dumps generated on error.
	//! @note an instance to this should remain in scope as long as dumps should be generated.
	class PdaExceptionHandler
	{
	public:
		//! Constructor, will setup (but not yet launch) the executable
		//! The crash context will only use reportingServer, applicationName, version, tag
		PdaExceptionHandler(const std::wstring exeLocation, const std::shared_ptr<pda::PdaCrashContext>& pdaCrashContext);

		//! Destructor will stop the child process (if running)
		~PdaExceptionHandler();

		//! will start the child process. Returns true if the handler is started
		bool startHandler();

		//! will stop the child process (if running). Returns true if the handler is stopped.
		bool stopHandler();

		//! will check if the child has been started.
		bool handlerIsStarted() const;

		//! used to add extra things to the command line call
		void setAdditionalArgs(const std::wstring extra);

	private:
		//! Location to the exe to launch
		std::wstring ExeLocation;

		//! Extra args for the command line call
		std::wstring AdditionalArgs;

#ifdef _WIN32
		//! HANDLE to child process
		HANDLE ExeProcessHandle;

		//! Holds info about crash reporting
		std::shared_ptr<pda::PdaCrashContext> PdaCrashContext;

		//! unique ptr to exception handler
		std::unique_ptr<google_breakpad::ExceptionHandler> ExceptionHandler;
#else
#error Implementation missing for OS
#endif
	};
};
