#include "Utility.h"
/*
This file contains the implementation for utilities
MIT License - 2019 - Charles Machalow
*/

namespace pda
{
	std::wstring toWString(const std::string s)
	{
		std::wstring retStr(s.begin(), s.end());
		return retStr;
	}
};