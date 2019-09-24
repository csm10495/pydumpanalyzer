/*
This file contains the implementation for utilities
MIT License - 2019 - Charles Machalow
*/

#include "Utility.h"

#ifdef _WIN32
#include <Windows.h>
#endif

#include <thread>

namespace pda
{
	std::wstring toWString(const std::string s)
	{
		std::wstring retStr(s.begin(), s.end());
		return retStr;
	}

	bool waitTillFileExists(const std::wstring filePath, std::chrono::seconds maxSeconds)
	{
		bool retVal = false;
#ifdef _WIN32

		DWORD attrs = INVALID_FILE_ATTRIBUTES;

		uint64_t deathTimeSeconds = std::chrono::duration_cast<std::chrono::seconds>(std::chrono::steady_clock().now().time_since_epoch()).count() + maxSeconds.count();

		while (std::chrono::duration_cast<std::chrono::seconds>(std::chrono::steady_clock().now().time_since_epoch()).count() < deathTimeSeconds)
		{
			attrs = GetFileAttributes(filePath.c_str());

			if (attrs != INVALID_FILE_ATTRIBUTES)
			{
				retVal = true;
				break;
			}

			std::this_thread::sleep_for(std::chrono::milliseconds(10));
		} 
#endif
		return retVal;
	}
};