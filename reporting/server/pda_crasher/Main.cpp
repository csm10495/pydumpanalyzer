/*
This file contains the implementations for pda's crasher
MIT License - 2019 - Charles Machalow
*/

#include <memory>
#include <string>

#include "Logging.h"
#include "PdaExceptionHandler.h"

std::wstring getCurrentExeFolder()
{
	wchar_t buffer[4096] = { 0 };

	DWORD retLength = GetModuleFileNameW(NULL, buffer, ARRAYSIZE(buffer));

	std::wstring path(buffer, retLength);
	return path.substr(0, path.find_last_of(L"\\/"));
}

int main(int argc, char* argv[])
{
	pda::setLogging(true);

	auto crashContext = std::make_shared<pda::PdaCrashContext>(
		L"http://localhost:5000/add",
		L"PDA Crasher"
		);

	auto exePath = getCurrentExeFolder() + L"/pda_server.exe";
	auto exceptionhandler = std::make_unique<pda::PdaExceptionHandler>(
		exePath,
		crashContext
		);

	if (!exceptionhandler->startHandler())
	{
		LOG("Failed to start handler");
		return EXIT_FAILURE;
	}

	// About to crash!
	char* p = (char*)NULL;
	*p = 5;

	return EXIT_SUCCESS;
}