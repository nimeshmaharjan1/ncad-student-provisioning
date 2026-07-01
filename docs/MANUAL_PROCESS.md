# Manual Student Provisioning Process

This document describes the **manual process** that was used before this automated system was built.
It exists here so that:
- Future developers understand what the system replaced and why.
- Provisioning can still be done manually if the automated pipeline fails.

---

## Step 1: Export and Prepare Student Data from Quercus

### Access Quercus
Open Quercus using the following URL:
https://eu-quercus.elluciancloud.com/app/ncad/f?p=1001:LOGIN::::

### Navigate to the Student Report
1. Click the 2nd Reporting card.
2. On the top right, click **AD HOC**.
3. On the next page, click on **Configure Reports** on the far right.
4. In the search box, enter: `all students 2025`
5. Two reports named **All Students 2025** will be displayed. Select the first report and ignore the second.
6. The report view page will open.

### Export 2025 Student Data
1. Ignore the filters and sorting options on the page.
2. On the right-hand side, locate the search box.
3. Enter: `2025`
4. Click **Apply**.
5. Locate and click **Download** icon at the top of the page.
6. Select **CSV**.
7. Save the file as: `2025_all_students.csv`
8. Save the file in the `Quercus_2025` folder.

### Export 2026 Student Data
1. In the search box, enter: `2026`
2. Click **Apply**.
3. Click **Download** and select **CSV**.
4. Save the file with an appropriate name.
5. Save the file in the `Quercus_2025` folder.

### Merge the Student Data
Open both CSV files and combine the 2025 and 2026 records into a single dataset.
Keep the 2025 records first and append the 2026 records below them.

### Create the Term Email Column
Create a new column called **Term Email**.
The student ID must always be represented as an 8-digit number with leading zeros where required.

Use the following Excel formula:
```
=TEXT(A2,"00000000")&"@student.ncad.ie"
```

Example:
- If the Student ID is: `123456`
- The resulting Term Email will be: `00123456@student.ncad.ie`

The Term Email field will be used as the unique identifier when comparing records across all systems.

### Remove Duplicate Records
After the Term Email column has been created, remove duplicate entries using the **Term Email** column so that each student appears only once.
This step must be completed before any sorting or filtering.

Excel **Remove Duplicates** keeps the first occurrence of a duplicate record. Since the 2025 records appear above the 2026 records, performing duplicate removal at this stage ensures the correct record is retained.

### Filter Student Status
1. Sort the data by the **Status** column.
2. Retain only the following statuses:
   - Registered
   - Recommended
3. Remove records with all other statuses.

### Sort by Course Code
Sort the data by the **Course Code** column.

The course types are identified as follows:
- Course codes below AD100 are **CEAD** (Part-Time Evening). *(To be rechecked.)*
- Course codes from AD100 to AD399 are **Undergraduate (UG)**.
- Course codes AD400 and above are **Postgraduate (PG)**.

### Remove NCAD Electives
Remove records where the course corresponds to **NCAD Electives**.
These students already have access through Canvas and do not require account creation.

### Save the Cleaned File
The Quercus data is now cleaned and ready for LDAP processing.

Save the file in the `Quercus_2025` folder using the naming convention:
- Working file: `YYYYMMDD_quercus`
- Final CSV file: `YYYYMMDD_quercus.csv`

Example: `20260617_quercus` / `20260617_quercus.csv`

---

## Step 2: Prepare the LDAP Import File

### Update the LDAP Reference File
Open the most recent previous LDAP export located in the `LDAP_2025` folder.
The file naming convention is:
```
pre_YYYYMMDD_ldap.csv
```
Example: `pre_20260612_ldap.csv`

This file contains all LDAP records created before 12 June 2026.

If LDAP import files have been created since the date of the previous reference file, merge those records into the previous reference file.

Example:
```
pre_20260612_ldap.csv
+ 20260616_ldap.csv
= pre_20260618_ldap.csv
```

Save the merged file using the current date.
This file becomes the new LDAP reference file and contains all LDAP records created before the current date.

### Populate with Quercus Data
1. Open the latest Quercus file: `YYYYMMDD_quercus.csv`
2. Open the updated LDAP reference file: `pre_YYYYMMDD_ldap.csv`
3. Using the existing LDAP file format and column headers, copy the relevant data from the Quercus file into the corresponding LDAP columns.
4. Map each Quercus field to its respective LDAP column and ensure the LDAP structure is preserved.
5. Append the Quercus records below the existing LDAP records.

### Remove Existing Students
Once all Quercus records have been added, select the entire dataset and choose:
**Data → Remove Duplicates**

Ensure that:
- **My data has headers** is selected.
- Only the **email_address** column is selected.

Since the existing LDAP records appear first, duplicate entries from Quercus will be removed.
The remaining records at the bottom represent students that do not already exist in LDAP.

### Create the New LDAP File
Copy only the new student records into a separate file.
Use the same column headers and format as the existing LDAP file.

These records will form the new LDAP import file:
```
YYYYMMDD_ldap.csv
```
Example: `20260618_ldap.csv`

### Format the Date of Birth (DOB) Column
1. Select the entire DOB column.
2. Right-click and select **Format Cells**.
3. Select **Custom**.
4. Enter the following format: `dd/mm/yyyy`
5. Click **OK**.

Example: `17/06/2001`

Ensure all Date of Birth values are displayed in this format before proceeding.

### Generate Passcodes
Open the following website:
https://www.correcthorsebatterystaple.net/index.html

Generate a passcode for each new student.
Example generated passcode: `Network-Decision-Feather-Creep-0`

1. Remove the hyphens so the passcode becomes: `NetworkDecisionFeatherCreep0`
2. Replace the final number with a random number to avoid possible conflicts with the letter I.
   Example: `NetworkDecisionFeatherCreep7`
3. If any generated passphrase contains inappropriate, offensive, or unsuitable words, discard it and generate a new passcode instead.
4. Do not modify individual words within a passphrase. Only fully regenerated passcodes are valid for use.
5. Add the completed passcode to the **Passcode** column for each new student record.

### Save the LDAP File
Save the completed file in the `LDAP_2025` folder using the naming convention:
- Working file: `YYYYMMDD_ldap`
- Final CSV file: `YYYYMMDD_ldap.csv`

Example: `20260618_ldap` / `20260618_ldap.csv`

### Upload the LDAP File
Upload the completed LDAP file using **SFTP**.

### Email Triangle Service Desk
After the upload is complete, email the **Triangle Service Desk** with the LDAP file.
Wait for confirmation that the accounts have been created successfully before sending any student communications.
Students must not be sent their login details until confirmation has been received, as Single Sign-On (SSO) will not function until the LDAP accounts have been created.

---

## Step 3: Google Workspace User Management (Student Accounts)

### Access Google Workspace Admin
Open the student domain admin portal:
Google Workspace Admin Console

Navigate to the **Users** section.

### Export Existing Google Users
1. Use the **Bulk User Download / Export Users** function.
2. Download the full user list as a CSV file.
3. The file is automatically saved to the local Downloads folder.

### Store Export File
Move the downloaded CSV file into:
`Google_2025`

### Review Suspended Accounts
1. Open the Google export file.
2. Filter users with **Status = Suspended**.
3. Copy these suspended users into a new worksheet.
4. Bring in the latest Quercus file: `YYYYMMDD_quercus.csv`
5. Highlight duplicates between the suspended users and Quercus records.
6. Check the Student ID in Quercus manually, one by one.
7. If a student should no longer be suspended (e.g. they have enrolled on a new course), reactivate the account.
8. After reactivation, add the student to the appropriate mailing group according to their student type:
   - CEAD
   - Undergraduate (UG)
   - Postgraduate (PG)
9. Also send the reset password — click **Generate Password Automatically** and send email to their personal email (located on the left side of the user view page).

### Compare with Quercus Data
1. Open the latest Quercus file.
2. Use **Term Email** (`studentnumber@student.ncad.ie`) as the unique identifier.
3. Compare Google users with Quercus records.
4. Identify users present in Quercus but not in Google Workspace.
5. Retain only these new students requiring account creation.

### Prepare Google Upload File
1. Ensure the file maintains the existing Google CSV structure and headers found inside `Email_2025 => to_upload_date` format file.
2. The new student records must follow the Google import format exactly.
3. Username format: `student_number@student.ncad.ie`
4. Set: **Force password change at next sign-in = TRUE**

### Generate Temporary Passwords
1. Open: https://www.uuidgenerator.net/
2. Generate one UUID for each new student.
3. Copy or download the generated values.
4. Paste each UUID into the **Password** column.
Each user must have a unique temporary password.

### Upload to Google Workspace
Upload the prepared CSV file using the bulk user upload/import function.
This creates new student accounts.

### Add Users to Mailing Groups
After account creation or account reactivation:
1. Add the student email address to the appropriate mailing list.
2. Search for the required Google Group.
3. Add users individually to the group.

Group assignment is based on student category:

| Student Type | Google Group |
|---|---|
| CEAD | NCAD CEAD 2025 |
| Undergraduate (UG) | NCAD Undergraduate 2025 |
| Postgraduate (PG) | NCAD Postgraduate 2025 |

Ensure each student is added to the correct group individually.

### Save File Convention
Store files in: `Email_2025`
- Working file: `to_upload_YYYYMMDD`
- Final file: `to_upload_YYYYMMDD`

---

## Step 4: Canvas Student Account Import (SIS)

### Access Canvas
Open the Canvas administration system.
*(Canvas URL/domain to be confirmed.)*

### Update the Canvas Reference File
Navigate to: `Canvas_2025\Students_canvas`

Open the most recent Canvas reference file:
```
canvas_all_pre_YYYYMMDD.csv
```
Example: `canvas_all_pre_20260616.csv`

If a Canvas import file has been created since the date of the previous reference file, merge those records:

Example:
```
canvas_all_pre_20260616.csv
+ 20260616_canvas.csv
= canvas_all_pre_20260618.csv
```

Create a new folder for the current date: `20260618_canvas`
Save the updated master file inside the new folder while preserving the existing Canvas format and structure.
This file becomes the new Canvas reference file.

### Compare with Quercus Data
1. Open the latest Quercus file: `YYYYMMDD_quercus.csv`
2. Open the updated Canvas reference file: `canvas_all_pre_YYYYMMDD.csv`
3. Using the existing Canvas file format and column headers, copy the relevant data from Quercus into the corresponding Canvas columns.
4. Map each Quercus field to its respective Canvas column and append the records below the existing Canvas records.
5. Select the entire dataset and choose: **Data → Remove Duplicates**
6. Ensure **My data has headers** is selected and only the **Term Email** column is selected.
7. Since the existing Canvas records appear first, duplicate entries from Quercus will be removed.
8. The remaining records at the bottom represent students that do not already exist in Canvas.

### Prepare Canvas SIS Import File
Copy only the new student records into a separate file.
Ensure the file matches the required Canvas SIS CSV structure and headers exactly.
Do not modify column names.
Username format: `student_number@student.ncad.ie`
Recheck duplicates before uploading.

### Save File Convention
- Folder: `YYYYMMDD_canvas`
- Working file: `YYYYMMDD_canvas`
- Final CSV file: `YYYYMMDD_canvas.csv`

Example: `20260618_canvas` / `20260618_canvas.csv`

### Upload to Canvas (SIS Import)
Upload the prepared CSV file using the **SIS Import** tool.
This creates new student accounts in Canvas.

### Notify Rene
After the SIS import is complete:
1. Upload the file using: filesender2.heanet.ie
2. Send the file to Rene.
3. State in the email that the password is the same as previously used.

### Post-Import Verification
1. Confirm SIS import completion.
2. Verify that new users have been created successfully.
3. Ensure no duplicate accounts exist for the same Term Email.

---

## Step 5: Library System Student Provisioning

### Access Quercus
Open Quercus and navigate to:
1. Click the **Students** card.
2. Click **AD HOC**.
3. Under **Configure Reports**, click **List Screen**.
4. Search for: `IT Support Library`
5. Two reports named **IT Support Library** will be displayed.
6. Select the first report and ignore the second.

### Export Library Data
Export both:
- 2025
- 2026

Save the files in: `Library_2025`

### Create a Temporary Working File
Merge the 2025 and 2026 exports into a single file.
Keep the 2025 records first and append the 2026 records below them.

Save this file as: `all_students_YYYYMMDD.csv`
Example: `all_students_20260618.csv`

*This file is used only to prepare and tidy the Quercus data. It is not uploaded to the Library system.*

### Clean the Data
Do the exact same steps as in Step 1 (Quercus) to only keep **Recommended** and **Registered** statuses.

The **barcode** should be the same as **idAtSource**.

### Recreate Term Email
1. Remove the existing Term Email column.
2. Create a new Term Email column using the **ID Number** field.
3. Student IDs must always be eight digits long and must use ID Number rather than LDAP ID.

Use:
```
=TEXT(F2,"00000000")&"@student.ncad.ie"
```

Example: `00123456@student.ncad.ie`
Populate the **Email** field using the Term Email values.

### Remove Duplicate Records
Before performing any sorting, remove duplicate records using the **Term Email** column.
This prevents records from the 2025 and 2026 exports from becoming intermixed.

### Categorize Student Type
Sort by **Course Code** and assign **Borrower Category**:
- Below AD100 → CEAD
- AD100 to AD399 → FTUG
- AD400 and above → FTPG
*(Higher Diploma classification to be confirmed.)*

### Remove Unnecessary Data
Remove:
- NCAD Electives
- Personal phone numbers
- Home addresses

### Validate Gender Values
Only the following values are permitted:
- MALE
- FEMALE
- UNKNOWN

Any other value must be changed to: **UNKNOWN**

### Verify Date Formats
Format all date columns using: `yyyy-mm-dd`
Verify:
- Course Start Date (`circRegistrationDate`)
- Course End Date (`oclcExpirationDate`)

### Create the New Library Upload File
1. Open the previous Library upload file (e.g. `20260616_library.csv`).
2. *This file is used as a reference/template only. Do not overwrite the previous file.*
3. Compare the column headers visually, as the Quercus field names and Library field names differ.
4. Copy the values from `all_students_20260618.csv` into their corresponding columns in the Library format.
5. Preserve the existing Library column names and structure.
6. Append the new records below the existing records.
7. Save the completed file as: `20260618_library.csv`

### Upload File
Upload `20260618_library.csv` using the Library SFTP process.
Separate SFTP instructions will be provided by John.

**Note:** The Library system automatically patches existing users and creates new users as required. Therefore, no comparison with previous Library uploads is required.

---

## Step 6: OpenAthens Account Provisioning

### Access OpenAthens Admin
1. Open: https://admin.openathens.net/?org=54803643#PresetSearch:type=AllAccounts
2. Sign in using the OpenAthens administrator account.

### Export Existing OpenAthens Accounts
1. Download the current list of all OpenAthens accounts.
2. Save the export in: `Athens_2025`

### Compare with Quercus Data
1. Open the latest Quercus file: `YYYYMMDD_quercus.csv`
2. Open the OpenAthens account export.
3. Use the **Term Email** column as the unique identifier.
4. Identify students present in Quercus but not present in OpenAthens.
5. Retain only the new students requiring OpenAthens accounts.

### Download the Bulk Upload Template
1. Navigate to: **Accounts → Bulk Upload**
2. Download the OpenAthens bulk upload template.

### Prepare the OpenAthens Upload File
1. Open the bulk upload template.
2. Rearrange the new student data into the template format.
3. Populate the following fields from Quercus:
   - Forename
   - Surname
   - Email Address (Term Email)
4. Set **Status** to: `Pending`
5. Ensure the **Expiry Date** field is formatted as: `yyyy-mm-dd`
6. Leave all other template values unchanged unless required.

### Recheck Data
1. Verify all email addresses use the Term Email format.
2. Verify all dates use the format: `yyyy-mm-dd`
3. Verify student names have been mapped correctly.
4. Recheck duplicates before upload.

### Save File Convention
Store files in: `Athens_2025`
- Working file: `YYYYMMDD_athens`
- Final CSV file: `YYYYMMDD_athens.csv`

Example: `20260618_athens` / `20260618_athens.csv`

### Upload the OpenAthens File
1. Upload the completed CSV using the OpenAthens **Bulk Upload** function.
2. Confirm the upload has completed successfully.
3. Verify that the new accounts have been created.

---

## Step 7: Send LDAP Credentials to Student Email Addresses

### Wait for LDAP Account Creation Confirmation
Wait for confirmation from the **Triangle Service Desk** that the LDAP accounts have been successfully created.
**Do not send any student communications before receiving confirmation.**

### Access Thunderbird
1. Open **Thunderbird**.
2. Use the account provided by John.
3. Open the **LDAP email template**.

### Prepare Recipient List
Use the LDAP file: `YYYYMMDD_ldap.csv` as the source of student email addresses.

### Send LDAP Credentials
1. Use Thunderbird **Tools → Mail Merge**.
2. Select the LDAP email template.
3. Merge using the LDAP file.
4. Send LDAP credentials to student email addresses.

*Further mail merge settings and manual steps will be documented later.*

---

## Step 8: Send Eduroam Wi-Fi Information

### Access Thunderbird
1. Open **Thunderbird**.
2. Use the account provided by John.
3. Open the **Eduroam email template**.

### Prepare Recipient List
Use the same LDAP file: `YYYYMMDD_ldap.csv` as the source of student email addresses.

### Send Eduroam Information
1. Use Thunderbird **Tools → Mail Merge**.
2. Select the Eduroam template.
3. Merge using the LDAP file.
4. Send the Eduroam Wi-Fi information to student email addresses.

*Further mail merge settings and manual steps will be documented later.*

---

## Step 9: Send Student Email Account Details to Personal Email Addresses

### Access Thunderbird
1. Open **Thunderbird**.
2. Use the account provided by John.
3. Open the **student email template**.

### Prepare Recipient List
Use the reference file: `to_mail` located in: `Email_2025`
This file contains the students' personal email addresses.

### Send Student Email Details
1. Use Thunderbird **Tools → Mail Merge**.
2. Select the student email template.
3. Use the `to_mail` file as the recipient source.
4. Send student email account details to the students' personal email addresses.

*Further mail merge settings and manual steps will be documented later.*
