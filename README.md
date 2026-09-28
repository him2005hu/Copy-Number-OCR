# Copy Number OCR to Excel

A beginner-friendly Python project that reads document or copy numbers from images using OCR and saves them into an Excel file.

## Project description

This project is designed for users who have a folder of document images and want to automatically extract numbers such as:

- Copy No
- Copy Number
- Serial No
- Serial Number
- Document No
- No.

The program reads each image, processes it with OpenCV, extracts text with Tesseract OCR, identifies the copy number, and saves the results into an Excel file.

## Features

- Reads JPG, JPEG, and PNG files from the `images` folder
- Preprocesses images before OCR
- Extracts useful text using Tesseract OCR
- Identifies document copy numbers from surrounding labels
- Saves results into Excel
- Marks duplicate copy numbers
- Handles missing or unreadable files gracefully
- Includes a simple CLI and a beginner-friendly Tkinter GUI
- Works entirely on the local computer

## Technologies used

- Python 3.12+
- OpenCV
- Tesseract OCR
- pytesseract
- Pandas
- OpenPyXL
- Pillow
- Tkinter

## Project structure

```text
Copy-Number-OCR/
│
├── images/
│   └── .gitkeep
│
├── output/
│   └── .gitkeep
│
├── ocr.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation steps

### 1. Install Python

Download and install Python 3.12 or newer from:

https://www.python.org/downloads/

During installation, make sure to check:

- "Add Python to PATH"

## Python setup in VS Code

1. Open VS Code
2. Create a folder called `Copy-Number-OCR`
3. Open the folder in VS Code
4. Create the files listed above
5. Open the terminal in VS Code

## Virtual environment setup

Run these commands in the VS Code terminal:

```bash
python -m venv venv
```

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\venv\Scripts\Activate.ps1
```

## Dependency installation

After activating the virtual environment, run:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Tesseract OCR installation for Windows

Install Tesseract from:

https://github.com/UB-Mannheim/tesseract/wiki

Then confirm the installation path:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

The project is configured to automatically detect this path if it exists. If your Tesseract installation is in a different folder, you can set:

```powershell
$env:TESSERACT_CMD = "C:\your\path\to\tesseract.exe"
```

or update the path in the code.

## How to add images

Place your JPG, JPEG, or PNG images in:

```text
images/
```

Example:

```text
images/copy1.jpg
images/copy2.png
images/copy3.jpeg
```

Do not commit real personal documents to GitHub.

## How to run the program

### Command-line version

```bash
python ocr.py
```

This will:

- read all images in the `images` folder
- OCR each image
- detect the likely document number
- write results to:

```text
output/copy_numbers.xlsx
```

### GUI version

```bash
python ocr.py --gui
```

The GUI allows the user to:

- choose an image folder
- click Process Images
- view OCR results
- open the generated Excel file

## Example Excel output

| Sr. No. | Image Name | Extracted Number | Status | Duplicate |
| ------- | ---------- | ---------------- | ------ | --------- |
| 1       | copy1.jpg  | 458721           | Found  | No        |
| 2       | copy2.jpg  | 782341           | Found  | No        |
| 3       | copy3.jpg  | Not Found        | Not Found | No     |

## Troubleshooting

### Tesseract not found
- Make sure Tesseract is installed
- Confirm the path is correct
- Check the environment variable `TESSERACT_CMD`
- Or update `WINDOWS_TESSERACT_PATH` in `ocr.py`

### OCR returns poor results
- Use clearer images
- Improve image quality
- Keep the copy number area large and readable
- Use high-contrast documents
- Avoid shadows and blur

### No images found
- Make sure files are inside the `images` folder
- Use `.jpg`, `.jpeg`, or `.png` files
- Check that the folder exists

### Excel file not created
- Make sure the `output` folder exists
- Confirm the program has permission to write files
- Re-run the script

## GitHub upload instructions

Run the following commands in the terminal:

```bash
git init
git add .
git commit -m "Initial OCR project"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## Privacy note

This project processes images locally on the user's computer only.

- No images are uploaded to any external server
- No document data is sent anywhere online
- Keep sensitive or private documents off GitHub
- Do not include real personal documents in the repository

## Notes

- This project is designed to be simple and beginner-friendly
- OCR works best on clear, high-contrast document scans
- The program focuses on labels like Copy No and Serial No
- It tries to avoid blindly taking the first number it sees

## Quick start

1. Create the project folder
2. Copy all files above into it
3. Create images and put them in `images/`
4. Open VS Code terminal
5. Activate the virtual environment
6. Install dependencies:

```bash
pip install -r requirements.txt
```

7. Run:

```bash
python ocr.py
```

or

```bash
python ocr.py --gui
```

If you want, I can also provide:
- a version with a stronger OCR matching strategy for difficult documents
- a batch-processing folder selector for multiple subfolders
- a version that exports additional metadata to Excel
