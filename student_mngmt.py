#!/usr/bin/env python3
"""
Student Management System - CLI (All features)
Stores student records (roll, name, marks) in students.csv
Features:
 - Add (auto roll)
 - Delete
 - Search (partial by roll/name)
 - Edit / Update
 - List All
 - Topper & Average
 - Export to PDF (reportlab) and CSV
"""

import csv
import os
from typing import List, Dict, Optional
from io import BytesIO

# Optional PDF export (reportlab). If not installed, export to PDF will show message.
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

CSV_FILE = "students.csv"
EXPORT_CSV_FILE = "students_export.csv"
FIELDNAMES = ["roll", "name", "marks"]
START_ROLL = 1001


def ensure_file_exists():
    """Create CSV file with header if it doesn't exist."""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def load_students() -> List[Dict[str, str]]:
    """Load all student records from CSV and return as list of dicts."""
    ensure_file_exists()
    with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def save_students(students: List[Dict[str, str]]) -> None:
    """Overwrite CSV with the provided student records."""
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for s in students:
            writer.writerow(s)


def generate_roll(students: List[Dict[str, str]]) -> str:
    """Generate next numeric roll (as string). Starts at START_ROLL if empty."""
    if not students:
        return str(START_ROLL)
    # safely convert numeric rolls and pick max; non-numeric rolls are ignored
    numeric_rolls = []
    for s in students:
        r = s.get("roll", "").strip()
        if r.isdigit():
            numeric_rolls.append(int(r))
    if not numeric_rolls:
        # fallback to count-based
        return str(START_ROLL + len(students))
    return str(max(numeric_rolls) + 1)


def find_by_roll(students: List[Dict[str, str]], roll: str) -> Optional[Dict[str, str]]:
    roll = roll.strip()
    for s in students:
        if s["roll"].strip() == roll:
            return s
    return None


def add_student():
    students = load_students()
    roll = generate_roll(students)
    print(f"\nGenerated Roll Number: {roll}")

    name = input("Enter Name: ").strip()
    if not name:
        print("Name cannot be empty. Aborting add.")
        return

    marks_input = input("Enter Marks (0-100): ").strip()
    try:
        # calculate digit-by-digit check: parse safely
        marks = float(marks_input)
        if marks < 0 or marks > 100:
            raise ValueError()
        marks_str = str(int(marks)) if marks.is_integer() else str(marks)
    except Exception:
        print("Invalid marks. Please use a number between 0 and 100. Aborting add.")
        return

    students.append({"roll": roll, "name": name, "marks": marks_str})
    save_students(students)
    print(f"Student added successfully with Roll {roll}.")


def delete_student():
    students = load_students()
    roll = input("Enter Roll Number to delete: ").strip()
    if not roll:
        print("Empty roll. Aborting delete.")
        return
    found = find_by_roll(students, roll)
    if not found:
        print(f"No student found with roll '{roll}'.")
        return

    confirm = input(f"Are you sure you want to delete {found['name']} (roll {roll})? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Delete cancelled.")
        return

    students = [s for s in students if s["roll"].strip() != roll]
    save_students(students)
    print("Student deleted and changes saved.")


def search_student():
    students = load_students()
    query = input("Search by Roll or Name (partial allowed): ").strip().lower()
    if not query:
        print("Empty query. Aborting search.")
        return
    results = []
    for s in students:
        if query in s["roll"].lower() or query in s["name"].lower():
            results.append(s)

    if not results:
        print("No matching student records found.")
        return

    print(f"\nFound {len(results)} result(s):")
    print("{:10} | {:30} | {:6}".format("Roll", "Name", "Marks"))
    print("-" * 52)
    for r in results:
        print("{:10} | {:30} | {:6}".format(r["roll"], r["name"], r["marks"]))
    print()


def list_students(show_header: bool = True):
    students = load_students()
    if not students:
        print("No student records yet.")
        return
    # try numeric sort
    try:
        students.sort(key=lambda x: int(x["roll"]))
    except Exception:
        students.sort(key=lambda x: x["roll"])

    if show_header:
        print("{:10} | {:30} | {:6}".format("Roll", "Name", "Marks"))
        print("-" * 52)
    for s in students:
        print("{:10} | {:30} | {:6}".format(s["roll"], s["name"], s["marks"]))
    print(f"\nTotal students: {len(students)}\n")


def edit_student():
    students = load_students()
    roll = input("Enter Roll Number to edit: ").strip()
    if not roll:
        print("Empty roll. Aborting edit.")
        return
    student = find_by_roll(students, roll)
    if not student:
        print(f"No student found with roll '{roll}'.")
        return

    print(f"Editing {student['name']} (Roll {student['roll']})")
    new_name = input(f"Enter new name [{student['name']}] (press Enter to keep): ").strip()
    if not new_name:
        new_name = student["name"]

    new_marks_input = input(f"Enter new marks [{student['marks']}] (press Enter to keep): ").strip()
    if not new_marks_input:
        new_marks_str = student["marks"]
    else:
        try:
            new_marks = float(new_marks_input)
            if new_marks < 0 or new_marks > 100:
                raise ValueError()
            new_marks_str = str(int(new_marks)) if new_marks.is_integer() else str(new_marks)
        except Exception:
            print("Invalid marks. Aborting edit.")
            return

    # apply update
    for s in students:
        if s["roll"].strip() == roll:
            s["name"] = new_name
            s["marks"] = new_marks_str
            break
    save_students(students)
    print("Student updated and saved.")


def topper_and_average():
    students = load_students()
    if not students:
        print("No records to calculate topper/average.")
        return

    marks_list = []
    for s in students:
        try:
            marks_list.append(float(s["marks"]))
        except Exception:
            marks_list.append(0.0)

    # average (computed step by step)
    total = 0.0
    for m in marks_list:
        total += m
    avg = total / len(marks_list)
    # round to 2 decimal places
    avg_rounded = round(avg, 2)

    max_marks = max(marks_list)
    toppers = [s for s in students if float(s.get("marks", 0)) == max_marks]

    print(f"\nAverage Marks: {avg_rounded}")
    print(f"Top Marks: {max_marks}")
    print("Topper(s):")
    for t in toppers:
        print(f" - {t['name']} (Roll {t['roll']}) — {t['marks']}")
    print()


def export_csv():
    students = load_students()
    if not students:
        print("No records to export.")
        return
    with open(EXPORT_CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(students)
    print(f"Exported to CSV file: {EXPORT_CSV_FILE}")


def export_pdf():
    if not REPORTLAB_AVAILABLE:
        print("reportlab is not installed. Install it with: pip install reportlab")
        return

    students = load_students()
    data = [["Roll", "Name", "Marks"]]
    for s in students:
        data.append([s["roll"], s["name"], s["marks"]])

    filename = "students_report.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elems = []
    elems.append(Paragraph("Student Management System - Report", styles["Title"]))
    elems.append(Spacer(1, 12))
    elems.append(Paragraph(f"Total students: {len(students)}", styles["Normal"]))
    elems.append(Spacer(1, 12))

    table = Table(data, colWidths=[60, 300, 60])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4B8BBE")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elems.append(table)
    doc.build(elems)
    print(f"PDF report generated: {filename}")


def show_menu():
    menu = """
Student Management System - CLI
1. Add Student
2. Delete Student
3. Search Student
4. Edit / Update Student
5. List All Students
6. Topper & Average
7. Export to PDF
8. Export to CSV
9. Exit
"""
    print(menu)


def main():
    ensure_file_exists()
    while True:
        show_menu()
        choice = input("Choose an option (1-9): ").strip()
        if choice == "1":
            add_student()
        elif choice == "2":
            delete_student()
        elif choice == "3":
            search_student()
        elif choice == "4":
            edit_student()
        elif choice == "5":
            list_students()
        elif choice == "6":
            topper_and_average()
        elif choice == "7":
            export_pdf()
        elif choice == "8":
            export_csv()
        elif choice == "9":
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid option. Enter number 1-9.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
