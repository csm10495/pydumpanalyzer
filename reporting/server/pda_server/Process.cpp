/*
This file contains the implementations for process management
MIT License - 2019 - Charles Machalow
*/

#include "Process.h"

#ifdef _WIN32
#include <Windows.h>
#endif

#include <thread>

namespace pda
{
	std::wstring getNamedPipeForPid(const uint32_t pid)
	{
		return L"\\\\.\\pipe\\pda_pid\\" + std::to_wstring(pid);
	}

	void waitForProcessExit(const uint32_t pid)
	{
#ifdef _WIN32
		HANDLE handle = OpenProcess(PROCESS_QUERY_INFORMATION, false, pid);
		if (!handle)
		{
			LOG("Unable to obtain handle to pid: " + std::to_string(pid));
			return;
		}
#endif

		while (true)
		{
#ifdef _WIN32
			DWORD exitCode = 0;
			bool success = GetExitCodeProcess(handle, &exitCode);

			if (!success)
			{
				LOG("Failed to GetExitCodeProcess");
				break;
			}

			if (exitCode != STILL_ACTIVE)
			{
				LOG("pid " + std::to_string(pid) + " is no longer active... exit code: " + std::to_string(exitCode));
				break;
			}
#else
#error Not implemented for non-Win32
#endif
			std::this_thread::sleep_for(std::chrono::seconds(1));
		}

#ifdef _WIN32
		CloseHandle(handle);
#endif
	}
};
