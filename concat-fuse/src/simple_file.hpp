// concat-fuse
// Copyright (C) 2015 Ingo Ruhnke <grumbel@gmail.com>
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

#ifndef HEADER_SIMPLE_FILE_HPP
#define HEADER_SIMPLE_FILE_HPP

#include <string>
#include <memory>

#include "file.hpp"

class SimpleFileStream;

class SimpleFile : public File
{
private:
  std::unique_ptr<SimpleFileStream> m_stream;

public:
  SimpleFile(const std::string& data);
  virtual ~SimpleFile();

  int getattr(const char* path, struct stat* stbuf) override;

  int open(const char* path, struct fuse_file_info* fi) override;
  int release(const char* path, struct fuse_file_info* fi) override;

  int read(const char* path, char* buf, size_t len, off_t offset,
           struct fuse_file_info* fi) override;

private:
  SimpleFile(const SimpleFile&) = delete;
  SimpleFile& operator=(const SimpleFile&) = delete;
};

#endif

/* EOF */
