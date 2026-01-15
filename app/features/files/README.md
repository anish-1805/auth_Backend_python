# File Upload Feature - Using Generators

This feature demonstrates the use of **Python generators** for memory-efficient file processing, specifically for PDF file uploads.

## 🎯 Purpose

The file upload feature was created to showcase the practical use of generators for:
- Reading large files without loading them entirely into memory
- Processing files in chunks for better performance
- Counting file statistics (size, chunks, lines) efficiently

## 🔧 How Generators Are Used

### 1. **Chunk-Based File Reading**
`@app/utils/file_reader.py:read_file_in_chunks_async()`

```python
async def read_file_in_chunks_async(file_path: str) -> AsyncGenerator[bytes, None]:
    async with aiofiles.open(file_path, mode="rb") as file:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            yield chunk  # ← Generator yields one chunk at a time
```

**Benefits:**
- Processes 10MB PDF without loading entire file into memory
- Yields 8KB chunks one at a time
- Memory usage stays constant regardless of file size

### 2. **File Length Counting**
`@app/utils/file_reader.py:count_file_length_async()`

```python
async def count_file_length_async(file_path: str) -> Dict[str, Any]:
    # For PDF files, count chunks using generator
    chunk_count = 0
    if file_extension == '.pdf':
        async for _ in read_file_in_chunks_async(file_path, chunk_size):
            chunk_count += 1  # ← Counts chunks without storing them
    
    return {
        "file_size_bytes": file_size,
        "total_chunks": chunk_count,
        ...
    }
```

**Benefits:**
- Counts chunks without storing file content
- Works with files of any size
- Returns detailed statistics

## 📡 API Endpoints

### 1. **Upload PDF File**
```http
POST /api/files/upload
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

file: <pdf_file>
```

**Response:**
```json
{
  "success": true,
  "message": "File 'document.pdf' uploaded and analyzed successfully",
  "file_stats": {
    "file_name": "document.pdf",
    "file_size_bytes": 1048576,
    "file_size_kb": 1024.0,
    "file_size_mb": 1.0,
    "total_chunks": 128,
    "file_type": ".pdf",
    "chunk_size_used": 8192
  }
}
```

### 2. **Analyze Uploaded File**
```http
GET /api/files/analyze/{file_name}
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "file_name": "document.pdf",
  "file_size_bytes": 1048576,
  "file_size_kb": 1024.0,
  "file_size_mb": 1.0,
  "total_chunks": 128,
  "file_type": ".pdf",
  "chunk_size_used": 8192
}
```

### 3. **List Uploaded Files**
```http
GET /api/files/list
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "files": [
    {
      "file_name": "document1.pdf",
      "file_size_bytes": 1048576,
      "total_chunks": 128,
      ...
    },
    {
      "file_name": "document2.pdf",
      "file_size_bytes": 2097152,
      "total_chunks": 256,
      ...
    }
  ],
  "total_files": 2
}
```

### 4. **Delete File**
```http
DELETE /api/files/delete/{file_name}
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "message": "File 'document.pdf' deleted successfully"
}
```

## 🔐 Security Features

1. **Authentication Required**: All endpoints require JWT authentication
2. **User Isolation**: Each user has their own upload directory
3. **File Type Validation**: Only PDF files allowed
4. **File Size Limit**: Maximum 10MB per file
5. **Unique File Names**: Automatic counter for duplicate names

## 📁 File Structure

```
uploads/
├── user_id_1/
│   ├── document.pdf
│   └── report.pdf
├── user_id_2/
│   └── presentation.pdf
```

## 🚀 Usage Example

### Using cURL:

```bash
# Upload a PDF file
curl -X POST http://localhost:5000/api/files/upload \
  -H "Authorization: Bearer <your_jwt_token>" \
  -F "file=@/path/to/document.pdf"

# List uploaded files
curl -X GET http://localhost:5000/api/files/list \
  -H "Authorization: Bearer <your_jwt_token>"

# Analyze a specific file
curl -X GET http://localhost:5000/api/files/analyze/document.pdf \
  -H "Authorization: Bearer <your_jwt_token>"

# Delete a file
curl -X DELETE http://localhost:5000/api/files/delete/document.pdf \
  -H "Authorization: Bearer <your_jwt_token>"
```

### Using Python:

```python
import requests

# Your JWT token
token = "your_jwt_token_here"
headers = {"Authorization": f"Bearer {token}"}

# Upload file
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:5000/api/files/upload",
        headers=headers,
        files=files
    )
    print(response.json())

# List files
response = requests.get(
    "http://localhost:5000/api/files/list",
    headers=headers
)
print(response.json())
```

## 🎓 Generator Benefits Demonstrated

### Memory Efficiency
```python
# Without Generator (Bad for large files)
def read_entire_file(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()  # ❌ Loads entire file into memory
    return content

# With Generator (Good for large files)
async def read_file_chunks(file_path):
    async with aiofiles.open(file_path, 'rb') as f:
        while True:
            chunk = await f.read(8192)
            if not chunk:
                break
            yield chunk  # ✅ Yields one chunk at a time
```

**Comparison:**
- **10MB PDF without generator**: 10MB memory usage
- **10MB PDF with generator**: 8KB memory usage (constant)

### Processing Large Files

```python
# Process 1GB file with constant memory
async for chunk in read_file_in_chunks_async("large_file.pdf"):
    # Process chunk (only 8KB in memory at a time)
    process_chunk(chunk)
```

## 📊 Performance Metrics

| File Size | Memory Usage (Without Generator) | Memory Usage (With Generator) |
|-----------|----------------------------------|-------------------------------|
| 1 MB      | 1 MB                             | 8 KB                          |
| 10 MB     | 10 MB                            | 8 KB                          |
| 100 MB    | 100 MB                           | 8 KB                          |
| 1 GB      | 1 GB (likely crashes)            | 8 KB                          |

## 🔍 How to Test

1. **Start the backend:**
   ```bash
   cd Backend_Python
   uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
   ```

2. **Login to get JWT token:**
   ```bash
   curl -X POST http://localhost:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "your@email.com", "password": "your_password"}'
   ```

3. **Upload a PDF file:**
   ```bash
   curl -X POST http://localhost:5000/api/files/upload \
     -H "Authorization: Bearer <token_from_step_2>" \
     -F "file=@/path/to/your/document.pdf"
   ```

4. **Check the response** - you'll see file statistics calculated using generators!

## 🎯 Key Takeaways

1. **Generators are memory-efficient**: Process large files without loading them entirely
2. **Async generators**: Perfect for I/O operations like file reading
3. **Practical use case**: File upload and analysis is a real-world scenario
4. **Scalable**: Can handle files of any size with constant memory usage

## 📝 Notes

- The `uploads/` directory is created automatically
- Files are organized by user ID for isolation
- Duplicate file names get automatic counters (e.g., `document_1.pdf`)
- All file operations use generators for memory efficiency
- The feature is production-ready with proper error handling
