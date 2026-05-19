from pathlib import Path
import pandas as pd

# ====== SETTINGS ======
in_dir = Path(r"ENTER YOUR PATH HERE")  # folder containing all CSV files
out_csv = in_dir / "ALL_UNIQUE_FEATURES_LIST.csv"  # final unique feature output table
conflict_txt = in_dir / "MZ_PEPTIDE_CONFLICT_REPORT.txt"  # report for m/z linked to multiple peptides
skipped_txt = in_dir / "SKIPPED_FILES_REPORT.txt"  # report for skipped/problematic files

pattern = "*.csv"  # file pattern to search

protein_col = "Protein"  # protein column name
mz_col = "mz"  # raw m/z column name
peptide_col = "Peptide"  # peptide sequence column name
mz_align_col = "mz_align"  # aligned m/z column name
desc_col = "desc"  # description column name
mod_col = "Modification"  # modification annotation column
adduct_col = "adduct"  # adduct annotation column

needed_cols = [protein_col, mz_col, peptide_col, mz_align_col, desc_col, mod_col, adduct_col]  # required columns for processing
# ======================

all_rows = []  # store cleaned rows from all files
skipped = []  # store skipped file information

files = sorted(in_dir.glob(pattern))  # collect all matching CSV files

for f in files:
    # Skip outputs/logs we generate in the same folder
    if f.name in {out_csv.name, conflict_txt.name, skipped_txt.name, "copy_log.csv"}:
        continue

    try:
        df = pd.read_csv(f, dtype=str, low_memory=False)  # read CSV as string to preserve formatting
    except UnicodeDecodeError:
        df = pd.read_csv(f, dtype=str, low_memory=False, encoding="latin1")  # fallback encoding for problematic files
    except Exception as e:
        skipped.append((f.name, f"read_failed: {e}"))  # record failed files
        continue

    missing_cols = [col for col in needed_cols if col not in df.columns]  # check for missing required columns
    if missing_cols:
        skipped.append((f.name, f"missing_cols: {missing_cols}"))  # skip files missing required columns
        continue

    tmp = df[needed_cols].copy()  # keep only required columns
    tmp["source_file"] = f.name  # track source file for conflict reporting

    # Clean spaces
    for col in needed_cols:
        tmp[col] = tmp[col].astype(str).str.strip()  # remove leading/trailing spaces

    # Remove empty / nan-like mz rows
    tmp = tmp[(tmp[mz_col] != "") & (tmp[mz_col].str.lower() != "nan")]  # remove invalid m/z rows

    # Clean other columns
    for col in [protein_col, peptide_col, mz_align_col, desc_col, mod_col, adduct_col]:
        tmp[col] = tmp[col].replace({"nan": "", "None": "", "<NA>": ""})  # standardize missing values

    # Remove exact duplicate rows within this file
    tmp = tmp.drop_duplicates()  # remove identical duplicated entries

    all_rows.append(tmp)  # add cleaned file data to master list

if not all_rows:
    raise RuntimeError("No valid files found with required columns. Check folder path and file pattern.")  # stop if no usable files found

master = pd.concat(all_rows, ignore_index=True)  # combine all cleaned files into one dataframe

# --------------------------------------------------
# Step 1: report mz values linked to multiple peptides
# --------------------------------------------------
conflict_lines = []  # store conflict report text

for mz_value, grp in master.groupby(mz_col, dropna=False):  # group rows by m/z value
    peptide_values = sorted(set(x.strip() for x in grp[peptide_col].fillna("") if x.strip() != ""))  # collect unique peptides per m/z

    if len(peptide_values) > 1:
        conflict_lines.append("=" * 100)
        conflict_lines.append(f"m/z CONFLICT: {mz_value}")
        conflict_lines.append(f"Distinct peptides found: {len(peptide_values)}")
        conflict_lines.append("Peptides:")
        for pep in peptide_values:
            conflict_lines.append(f"  - {pep}")  # list all peptides associated with this m/z
        conflict_lines.append("")
        conflict_lines.append("Rows involved:")
        for _, row in grp[[mz_col, protein_col, peptide_col, mod_col, adduct_col, mz_align_col, desc_col, "source_file"]].drop_duplicates().iterrows():
            conflict_lines.append(
                f"  file={row['source_file']} | Protein={row[protein_col]} | "
                f"Peptide={row[peptide_col]} | Mod={row[mod_col]} | Adduct={row[adduct_col]} | "
                f"mz_align={row[mz_align_col]} | desc={row[desc_col]}"
            )  # record all rows involved in this m/z conflict
        conflict_lines.append("")

if conflict_lines:
    with open(conflict_txt, "w", encoding="utf-8") as fh:
        fh.write("\n".join(conflict_lines))  # save detailed conflict report
    print(f"Conflict report written: {conflict_txt}")
else:
    with open(conflict_txt, "w", encoding="utf-8") as fh:
        fh.write("No m/z to peptide conflicts found.\n")  # save empty conflict report
    print(f"No conflicts found. Report written: {conflict_txt}")

# --------------------------------------------------
# Step 2: keep all unique feature rows
# --------------------------------------------------
# Keep unique combinations including modification and adduct
final = master.drop_duplicates(
    subset=[protein_col, mz_col, peptide_col, mod_col, adduct_col, mz_align_col, desc_col],
    keep="first"
).copy()  # remove duplicated feature combinations

# Sort numerically by mz if possible
final["_mz_num"] = pd.to_numeric(final[mz_col], errors="coerce")  # create numeric m/z column for sorting
final = final.sort_values(
    by=["_mz_num", mz_col, peptide_col, protein_col],
    na_position="last"
).drop(columns=["_mz_num", "source_file"])  # sort features and remove helper columns

# Save final output
final.to_csv(out_csv, index=False)  # export final unique feature table

print(f"Done. Unique feature rows: {len(final)}")
print(f"Saved feature table: {out_csv}")

# --------------------------------------------------
# Step 3: write skipped file report
# --------------------------------------------------
if skipped:
    with open(skipped_txt, "w", encoding="utf-8") as fh:
        for name, reason in skipped:
            fh.write(f"{name}\t{reason}\n")  # write skipped file name and reason
    print(f"Some files were skipped. See: {skipped_txt}")
