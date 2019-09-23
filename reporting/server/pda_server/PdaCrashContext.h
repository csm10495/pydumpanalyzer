/*
This file contains the headers for the PdaCrashContext object
MIT License - 2019 - Charles Machalow
*/

#pragma once

#include <memory>
#include <string>

namespace pda
{
	//! This represents the context around a crash for reporting
	class PdaCrashContext
	{
	public:
		//! Constructor taking in required components
		PdaCrashContext(const std::wstring reportingServer, const std::wstring applicationName);

		//! Used to set a tag for this crash
		void setTag(const std::wstring tag);

		//! Used to set an application version for this crash
		void setApplicationVersion(const std::wstring version);

		//! sets the location for a symbols file
		void setSymbolsFilePath(const std::wstring path);

		//! sets the location for an executable file
		void setExecutableFilePath(const std::wstring path);

		//! sets the location for a crash dump file
		void setCrashDumpFilePath(const std::wstring path);

		//! Reports this crash / context to the endpoint
		bool report() const;

	private:
		/* Strings */

		//! the server to report to
		std::unique_ptr<std::wstring> ReportingServer;

		//! the name of the application to report the crash as
		std::unique_ptr<std::wstring> ApplicationName;

		//! the tag for the crash
		std::unique_ptr<std::wstring> Tag;

		//! the application version
		std::unique_ptr<std::wstring> ApplicationVersion;

		/* File Paths */

		//! Path to symbols file
		std::unique_ptr<std::wstring> SymbolsFile;

		//! Path to executable file file
		std::unique_ptr<std::wstring> ExecutableFile;

		//! Path to executable file file
		std::unique_ptr<std::wstring> CrashDumpFile;
	};
};