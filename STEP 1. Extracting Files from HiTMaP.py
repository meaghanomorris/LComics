from pathlib import Path
import shutil

# ===== 1. Root folder containing all "XXXX finished" folders =====
# This is the top-level directory containing all processed HiTMaP output folders. The script recursively searches through every subfolder inside this directory.
root = Path(r"E:\Finished Core")


# ===== 2. Create destination folder on Desktop =====
# Path.home() automatically detects the current user's home directory, making the script portable across different computers and usernames.
desktop = Path.home() / "Desktop"

# Create a centralized output folder to collect all Peptide_Summary files.
dest = desktop / "All_Peptide_Summaries"

# Create the folder if it does not already exist. parents=True allows parent folder creation and exist_ok=True prevents errors if the folder already exists.
dest.mkdir(parents=True, exist_ok=True)

print(f"Saving files to: {dest}")


# ===== 3. Recursively search for all Peptide_Summary CSV files =====
# rglob() performs a recursive search through all subfolders under "root". The wildcard pattern searches for any CSV beginning with: "Peptide_Summary"

# Example matches: Peptide_Summary.csv, Peptide_Summary_Updated.csv
for peptide_file in root.rglob("Peptide_Summary*.csv"):

    # ===== 4. Navigate folder hierarchy =====
    # peptide_file.parent returns the folder directly containing the CSV file, typically the "Summary" folder.
    summary_folder = peptide_file.parent

    # Move one level upward from the Summary folder, typically corresponding to the sample folder.
    sample_folder = summary_folder.parent

    # Move another level upward, typically corresponding to the main "XXXX finished" core folder.
    core_folder = sample_folder.parent


    # ===== 5. Extract folder names for standardized renaming =====
    # .name extracts only the final folder name from the path, while replace(" ", "_") converts spaces into underscores for cleaner filenames.
    core_name = core_folder.name.replace(" ", "_")

    # Example: "1 1 GM" becomes "1_1_GM"
    sample_name = sample_folder.name.replace(" ", "_")


    # ===== 6. Build standardized output filename =====
    # Combine the core folder name, sample folder name, and file identifier into one unique filename to prevent overwriting files during centralized collection.
    new_name = f"{core_name}_{sample_name}_Peptide_Summary.csv"

    # Create the full destination path for the copied file.
    target = dest / new_name


    # ===== 7. Display copy progress =====
    # Print both the original file path and the destination path to help track processing progress and troubleshoot folder structure issues.
    print(f"Copying:\n {peptide_file}\n -> {target}")


    # ===== 8. Copy file while preserving metadata =====
    # shutil.copy2() copies the file while preserving metadata such as timestamps and modification dates.
    shutil.copy2(peptide_file, target)


# ===== 9. Final completion message =====
print("Done!")
