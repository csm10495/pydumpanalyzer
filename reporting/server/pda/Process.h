/*
This file contains the headers for process management
MIT License - 2019 - Charles Machalow
*/

#pragma once

#include <string>

#include "Logging.h"

namespace pda
{
	//! gets the win32 pipe name for the given pid (the pid is the process being monitored for crashes)
	std::wstring getNamedPipeForPid(const uint32_t pid);

	//! Waits for the given process pid to exit (and no longer be running)
	void waitForProcessExit(const uint32_t pid);
}