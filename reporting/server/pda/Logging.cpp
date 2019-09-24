/*
This file contains the implementations for logging
MIT License - 2019 - Charles Machalow
*/

#include "Logging.h"

#include <iostream>

//! singleton enable/disable switch for logging
bool loggingEnabled = false;

namespace pda
{
	namespace detail
	{
		void log(const std::string msg)
		{
			if (loggingEnabled)
			{
				std::clog << msg << std::endl;
			}
		}
		
		void log(const std::wstring msg)
		{
			if (loggingEnabled)
			{
				std::wclog << msg << std::endl;
			}
		}

		void log(std::map<std::wstring, std::wstring> mapOfStrings)
		{
			std::wstring buildStr = L"";
			for (auto& itr : mapOfStrings)
			{
				buildStr += itr.first + L" -> " + itr.second + L"\n";
			}

			log(buildStr);
		}
	}

	void setLogging(bool enabled)
	{
		loggingEnabled = enabled;
	}
}

