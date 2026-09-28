from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from tkinter import END, StringVar, Tk, filedialog, messagebox, scrolledtext, ttk

import cv2
import pandas as pd
import pytesseract
from PIL import Image, UnidentifiedImageError

# -----------------------------
# Configuration
# -----------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
IMAGES_DIR = PROJECT_ROOT / "images"
OUTPUT_DIR = PROJECT_ROOT / "output"
EXCEL_FILE = OUTPUT_DIR / "copy_numbers.xlsx"

# Default Windows Tesseract path.
WINDOWS_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Label patterns focused on copy/document number fields.
LABEL_PATTERNS = [
    r"(?i)(copy\s*(?:no|number))\s*[:\-]?\s*([0-9][0-9\s,./-]{3,20})",
    r"(?i)(serial\s*(?:no|number))\s*[:\-]?\s*([0-9][0-9\s,./-]{3,20})",
    r"(?i)(document\s*(?:no|number))\s*[:\-]?\s*([0-9][0-9\s,./-]{3,20})",
    r"(?i)(doc\s*(?:no|number))\s*[:\-]?\s*([0-9][0-9\s,./-]{3,20})",
    r"(?i)(no\.? )\s*[:\-]?\s*([0-9][0-9\s,./-]{3,20})",
    r"(?i)(number)\s*[:\-]?\s*([0-9][0-9\s,./-]{3,20})",
]

# -----------------------------
# Helper functions
# -----------------------------

def configure_tesseract():
    """Set the Tesseract path if it is available.

    This lets the program work on Windows without hard-coding the path in multiple places.
    """
    custom_path = os.environ.get("TESSERACT_CMD")
    if custom_path and os.path.exists(custom_path):
        pytesseract.pytesseract.tesseract_cmd = custom_path
        return

    if os.path.exists(WINDOWS_TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = WINDOWS_TESSERACT_PATH


def normalize_number(raw_value: str) -> str:
    """Convert OCR text like '45 8721' or '45,8721' into digits only."""
    cleaned = re.sub(r"[^0-9]", "", raw_value or "")
    if 4 <= len(cleaned) <= 20:
        return cleaned
    return ""


def preprocess_image(image_path: Path):
    """Preprocess the image before OCR.

    Steps:
    - convert to grayscale
    - enlarge if needed
    - denoise
    - threshold
    - improve contrast
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    except Exception as exc:
        raise ValueError(f"Unable to read image {image_path}: {exc}") from exc

    if image is None:
        raise ValueError(f"Unreadable or corrupt image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if gray.shape[0] < 1000 or gray.shape[1] < 1000:
        scale = 2.0
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    gray = cv2.equalizeHist(gray)

    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    processed = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, kernel)

    return processed


def extract_text(image_path: Path) -> str:
    """Run OCR on the processed image and return raw OCR text."""
    processed = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed, config="--psm 6")
    return text


def find_best_number_from_text(ocr_text: str) -> str:
    """Search for the most likely copy/document number from OCR text.

    Strategy:
    1. Look for known labels such as Copy No, Serial No, Document No.
    2. If found, extract nearby numeric values.
    3. If no labeled match is found, use a fallback numeric pattern.
    4. Do not blindly accept the first number found.
    """
    if not ocr_text or not ocr_text.strip():
        return "Not Found"

    lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
    candidate_scores = []

    for line in lines:
        for pattern in LABEL_PATTERNS:
            matches = re.finditer(pattern, line, flags=re.IGNORECASE)
            for match in matches:
                label = (match.group(1) or "").lower()
                number_text = match.group(2) or ""
                cleaned = normalize_number(number_text)

                if not cleaned:
                    continue

                score = 100
                if "copy" in label:
                    score += 30
                if "serial" in label:
                    score += 30
                if "document" in label:
                    score += 30
                if "doc" in label:
                    score += 20
                if "number" in label:
                    score += 15
                if "no" in label:
                    score += 10

                if 6 <= len(cleaned) <= 12:
                    score += 15
                elif 4 <= len(cleaned) < 6:
                    score += 5

                candidate_scores.append((score, cleaned))

    if not candidate_scores:
        all_numbers = re.findall(r"\b\d[\d\s,./-]{3,20}\d\b", ocr_text)
        for value in all_numbers:
            cleaned = normalize_number(value)
            if not cleaned:
                continue

            score = 20
            if 6 <= len(cleaned) <= 12:
                score += 10
            candidate_scores.append((score, cleaned))

    if not candidate_scores:
        return "Not Found"

    candidate_scores.sort(key=lambda x: x[0], reverse=True)
    best = candidate_scores[0][1]

    if len(best) < 4 or len(best) > 20:
        return "Not Found"

    return best


def extract_number(image_path: Path) -> str:
    """Extract the copy/document number from one image."""
    try:
        ocr_text = extract_text(image_path)
    except UnidentifiedImageError:
        return "Not Found"
    except Exception:
        return "Not Found"

    if not ocr_text or not ocr_text.strip():
        return "Not Found"

    number = find_best_number_from_text(ocr_text)
    return number


def save_to_excel(records: list[dict], file_path: Path):
    """Save processing results to Excel."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(
        records,
        columns=["Sr. No.", "Image Name", "Extracted Number", "Status", "Duplicate"],
    )

    df.to_excel(file_path, index=False)
    return df


def process_images(images_dir: Path = IMAGES_DIR, output_file: Path = EXCEL_FILE):
    """Process all images in a folder and save results to Excel."""
    if not images_dir.exists():
        print(f"Error: images folder does not exist: {images_dir}")
        return pd.DataFrame(columns=["Sr. No.", "Image Name", "Extracted Number", "Status", "Duplicate"])

    image_files = []
    allowed_exts = {".jpg", ".jpeg", ".png"}

    for item in sorted(images_dir.iterdir()):
        if item.is_file() and item.suffix.lower() in allowed_exts:
            image_files.append(item)

    if not image_files:
        print(f"No JPG, JPEG, or PNG images found in: {images_dir}")
        return pd.DataFrame(columns=["Sr. No.", "Image Name", "Extracted Number", "Status", "Duplicate"])

    results = []

    for index, image_path in enumerate(image_files, start=1):
        print(f"\nProcessing: {image_path.name}")

        try:
            extracted_number = extract_number(image_path)
            status = "Found" if extracted_number != "Not Found" else "Not Found"
            print(f"Extracted Number: {extracted_number}")
            print(f"Status: {status}")
        except Exception as exc:
            extracted_number = "Not Found"
            status = "Not Found"
            print(f"Error processing image: {exc}")
            print(f"Status: {status}")

        results.append(
            {
                "Sr. No.": index,
                "Image Name": image_path.name,
                "Extracted Number": extracted_number,
                "Status": status,
                "Duplicate": "No",
            }
        )

    counts = {}
    for row in results:
        number = row["Extracted Number"]
        if number and number != "Not Found":
            counts[number] = counts.get(number, 0) + 1

    for row in results:
        number = row["Extracted Number"]
        row["Duplicate"] = "Yes" if number in counts and counts[number] > 1 else "No"

    save_to_excel(results, output_file)

    print("\nProcessing complete.")
    print("Excel file created:")
    print(output_file)

    return pd.DataFrame(results, columns=["Sr. No.", "Image Name", "Extracted Number", "Status", "Duplicate"])


# -----------------------------
# GUI
# -----------------------------

class CopyNumberOCRGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Copy Number OCR to Excel")
        self.root.geometry("900x600")

        self.images_folder = IMAGES_DIR
        self.folder_var = StringVar(value=str(self.images_folder))

        title = ttk.Label(root, text="Copy Number OCR to Excel", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(20, 10))

        folder_frame = ttk.Frame(root)
        folder_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(folder_frame, text="Image Folder:").pack(side="left", padx=(0, 10))
        ttk.Entry(folder_frame, textvariable=self.folder_var, width=60).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_frame, text="Browse", command=self.select_folder).pack(side="left", padx=(10, 0))

        action_frame = ttk.Frame(root)
        action_frame.pack(fill="x", padx=20, pady=10)

        ttk.Button(action_frame, text="Process Images", command=self.process_images_gui).pack(side="left")
        ttk.Button(action_frame, text="Open Excel File", command=self.open_excel_file).pack(side="left", padx=(10, 0))

        self.output_box = scrolledtext.ScrolledText(root, wrap="word", width=120, height=25)
        self.output_box.pack(padx=20, pady=(10, 20), fill="both", expand=True)

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select a folder containing document images")
        if folder:
            self.images_folder = Path(folder)
            self.folder_var.set(str(self.images_folder))

    def process_images_gui(self):
        if not self.images_folder.exists():
            messagebox.showerror("Folder not found", f"Selected folder does not exist:\n{self.images_folder}")
            return

        self.output_box.delete("1.0", END)
        self.output_box.insert(END, "Starting OCR...\n")

        try:
            df = process_images(self.images_folder, EXCEL_FILE)
            self.output_box.insert(END, "\n\nResults:\n")
            self.output_box.insert(END, df.to_string(index=False))
            self.output_box.insert(END, "\n\nDone.")
        except Exception as exc:
            messagebox.showerror("Processing Error", f"An unexpected error occurred:\n{exc}")
            self.output_box.insert(END, f"\nError: {exc}")

    def open_excel_file(self):
        if not EXCEL_FILE.exists():
            messagebox.showinfo("File not found", "No Excel file has been created yet.")
            return

        try:
            if sys.platform.startswith("win"):
                os.startfile(str(EXCEL_FILE))
            else:
                os.system(f"xdg-open {EXCEL_FILE}")
        except Exception as exc:
            messagebox.showerror("Open Error", f"Unable to open Excel file:\n{exc}")


# -----------------------------
# CLI entry point
# -----------------------------

def main():
    configure_tesseract()

    if len(sys.argv) > 1 and sys.argv[1].lower() in {"--gui", "-g", "gui"}:
        root = Tk()
        app = CopyNumberOCRGUI(root)
        root.mainloop()
        return

    print("Starting Copy Number OCR...")
    process_images(IMAGES_DIR, EXCEL_FILE)


if __name__ == "__main__":
    main()
