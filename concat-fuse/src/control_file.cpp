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

#include "control_file.hpp"

#include <fuse.h>
#include <stdint.h>
#include <sys/stat.h>

#include "glob_file_list.hpp"
#include "multi_file.hpp"
#include "simple_directory.hpp"
#include "simple_file_list.hpp"
#include "util.hpp"
#include "zip_file.hpp"

ControlFile::ControlFile(SimpleDirectory& directory, Mode mode) :
  m_directory(directory),
  m_mode(mode),
  m_tmpbuf()
{
}

ControlFile::~ControlFile()
{
}

int
ControlFile::getattr(const char* path, struct stat* stbuf)
{
  stbuf->st_mode = S_IFREG | 0644;
  stbuf->st_nlink = 2;
  stbuf->st_size = 0;
  return 0;
}

int
ControlFile::open(const char* path, struct fuse_file_info* fi)
{
  if ((fi->flags & O_ACCMODE) == O_WRONLY)
  {
    fi->fh = m_tmpbuf.store(std::string());
    fi->direct_io = 1;

    log_debug("ControlFile::open {}", fi->fh);

    return 0;
  }
  else
  {
    return -EACCES;
  }
}

int
ControlFile::write(const char* path, const char* buf, size_t len, off_t offset,
                   struct fuse_file_info* fi)
{
  m_tmpbuf.get(fi->fh).append(buf, len);
  return static_cast<int>(len);
}

int
ControlFile::truncate(const char* path, off_t offsite)
{
  return 0;
}

int
ControlFile::release(const char* path, struct fuse_file_info* fi)
{
  std::string data = m_tmpbuf.drop(fi->fh);
  std::string sha1 = sha1sum(data);

  log_debug("RECEIVED: {}", sha1);

  auto it = m_directory.get_files().find(sha1);
  if (it != m_directory.get_files().end())
  {
    if (MultiFile* multi_file = dynamic_cast<MultiFile*>(it->second.get()))
    {
      multi_file->refresh();
    }
    return 0;
  }
  else
  {
    switch(m_mode)
    {
      case GLOB_MODE:
        m_directory.add_file(sha1,
                             std::make_unique<MultiFile>(std::make_unique<GlobFileList>(split(data, '\0'))));
        return 0;

      case LIST_MODE:
        m_directory.add_file(sha1,
                             std::make_unique<MultiFile>(std::make_unique<SimpleFileList>(split(data, '\0'))));
        return 0;

      case ZIP_MODE:
        m_directory.add_file(sha1, std::make_unique<ZipFile>(data));
        return 0;

      default:
        return 0;
    }
  }
}

/* EOF */
