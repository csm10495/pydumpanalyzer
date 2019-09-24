/*
This file contains the headers for utilities
MIT License - 2019 - Charles Machalow
*/

#pragma once

#include <chrono>
#include <string>

namespace pda
{
	//! Converts a string to a wstring
	std::wstring toWString(const std::string s);

	//! Attempts to wait up to the given number of seconds for the file to appear.
	//! If the file doesn't exist by the end of the given maxSeconds, return false (else true).
	bool waitTillFileExists(const std::wstring filePath, std::chrono::seconds maxSeconds);
};