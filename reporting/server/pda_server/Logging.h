/*
This file contains the headers for logging
MIT License - 2019 - Charles Machalow
*/

#pragma once

#include <map>
#include <string>

#define LOG(msg) pda::detail::log(msg)

namespace pda
{
	namespace detail
	{
		//! log helper function (will log if logging is enabled)
		//! @warning do not call these directly
		void log(const std::string msg);

		//! log helper function (will log if logging is enabled)
		//! @warning do not call these directly
		void log(const std::wstring msg);

		//! log helper function for logging a map of strings (will log if logging is enabled)
		//! @warning do not call these directly
		void log(std::map<std::wstring, std::wstring> mapOfStrings);
	}

	//! if true is given, logging will be enabled.
	void setLogging(bool enabled);
};
