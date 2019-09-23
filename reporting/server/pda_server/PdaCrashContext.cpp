/*
This file contains the implementations for the PdaCrashContext object
MIT License - 2019 - Charles Machalow
*/

#include "Logging.h"
#include "PdaCrashContext.h"

#include "common/windows/http_upload.h"

#include <chrono>

namespace pda
{
	PdaCrashContext::PdaCrashContext(const std::wstring reportingServer, const std::wstring applicationName)
	{
		this->ReportingServer = std::make_unique<std::wstring>(reportingServer);
		this->ApplicationName = std::make_unique<std::wstring>(applicationName);
	}

	void PdaCrashContext::setTag(const std::wstring tag)
	{
		this->Tag = std::make_unique<std::wstring>(tag);
	}

	void PdaCrashContext::setApplicationVersion(const std::wstring version)
	{
		this->ApplicationVersion = std::make_unique<std::wstring>(version);
	}

	void PdaCrashContext::setSymbolsFilePath(const std::wstring path)
	{
		this->SymbolsFile = std::make_unique<std::wstring>(path);
	}

	void PdaCrashContext::setExecutableFilePath(const std::wstring path)
	{
		this->ExecutableFile = std::make_unique<std::wstring>(path);
	}

	void PdaCrashContext::setCrashDumpFilePath(const std::wstring path)
	{
		this->CrashDumpFile = std::make_unique<std::wstring>(path);
	}

	bool PdaCrashContext::report() const
	{
		LOG(L"Starting to report to: " + *this->ReportingServer);
		std::map<std::wstring, std::wstring> parameters;
		std::map<std::wstring, std::wstring> files;

		/* Parameters */
#ifdef _WIN32
		parameters[L"OperatingSystem"] = L"Windows";
#else
#error Undefined Operating System
#endif

		parameters[L"Application"] = *this->ApplicationName;

		if (this->Tag)
		{
			parameters[L"Tag"] = *this->Tag;
		}

		if (this->ApplicationVersion)
		{
			parameters[L"ApplicationVersion"] = *this->ApplicationVersion;
		}

		LOG("Parameters:");
		LOG(parameters);

		/* Files */

		if (this->SymbolsFile)
		{
			parameters[L"SymbolsFile"] = *this->SymbolsFile;
		}

		if (this->ExecutableFile)
		{
			parameters[L"ExecutableFile"] = *this->ExecutableFile;
		}

		if (this->CrashDumpFile)
		{
			parameters[L"CrashDumpFile"] = *this->CrashDumpFile;
		}

		LOG("Files:");
		LOG(files);

		int timeoutMs = static_cast<int>(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::minutes(5)).count());
		int responseCode;
		std::wstring responseBody;

		bool result = google_breakpad::HTTPUpload::SendMultipartPostRequest(
			*this->ReportingServer,
			parameters,
			files,
			&timeoutMs,
			&responseBody,
			&responseCode
		);

		LOG(L"Response Code:" + std::to_wstring(responseCode));
		LOG(L"Response body:" + responseBody);

		return result;
	}
};

