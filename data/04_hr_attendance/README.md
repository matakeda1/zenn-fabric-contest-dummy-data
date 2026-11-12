# 04_hr_attendance　人事・勤怠

部署・従業員・日次勤怠・残業申請・研修受講・退職者。2024-11〜2026-10。

全体の説明はリポジトリ直下の README.md、全列の定義は docs/data_dictionary.md を参照してください。

## ファイル

| ファイル | 行数 | サイズ |
|---|---:|---:|
| `04_hr_attendance/attendance.csv` | 194,821 | 22.9 MB |
| `04_hr_attendance/departments.csv` | 38 | 0.0 MB |
| `04_hr_attendance/employees.csv` | 628 | 0.1 MB |
| `04_hr_attendance/overtime_requests.csv` | 49,852 | 5.8 MB |
| `04_hr_attendance/resignations.csv` | 201 | 0.0 MB |
| `04_hr_attendance/training_courses.csv` | 16 | 0.0 MB |
| `04_hr_attendance/training_records.csv` | 3,986 | 0.2 MB |

### 部署（`departments`）

本社部門・法人営業・店舗・工場・物流センターの部署。

- ファイル: `04_hr_attendance/departments.csv`
- 行数: 38
- 主キー: `department_id`
- 外部キー: site_id → 05 sites

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `department_id` | 文字列 | 部署 ID | D100 |
| `department_name` | 文字列 | 部署名 | 経営企画部 |
| `division` | 文字列 | 本部 | 本社部門 |
| `site_id` | 文字列 | 勤務地の拠点 ID | H01 |
| `parent_department_id` | 文字列 | 上位部署 ID | D200 |
| `established_date` | 日付 | 設置日（新店など） | 2016-04-01 |
| `abolished_date` | 日付 | 廃止日（閉店した店舗） | 2025-12-28 |

### 従業員（`employees`）

2024-11 以降に在籍した従業員（退職者を含む）。氏名は架空。

- ファイル: `04_hr_attendance/employees.csv`
- 行数: 628
- 主キー: `employee_id`
- 外部キー: department_id → departments, manager_employee_id → employees

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `employee_id` | 文字列 | 従業員 ID | E10001 |
| `last_name` | 文字列 | 姓（架空） | 松尾 |
| `first_name` | 文字列 | 名（架空） | 明美 |
| `gender` | 文字列 | 性別 | 女性 |
| `birth_date` | 日付 | 生年月日 | 1973-05-05 |
| `hire_date` | 日付 | 入社日 | 2024-09-19 |
| `hire_type` | 文字列 | 新卒 / 中途 / パート採用 | 新卒 |
| `employment_type` | 文字列 | 正社員 / 契約社員 / パート・アルバイト | 正社員 |
| `department_id` | 文字列 | 所属部署 ID（現在または退職時） | D100 |
| `site_id` | 文字列 | 勤務地の拠点 ID | H01 |
| `job_title` | 文字列 | 役職 | 部長 |
| `grade` | 文字列 | 等級（G1〜G7、パートは P） | G6 |
| `base_salary_monthly` | 整数 | 月額基本給（円、正社員・契約社員） | 500000.0 |
| `hourly_wage` | 整数 | 時給（円、パート・アルバイト） | 1310.0 |
| `manager_employee_id` | 文字列 | 上長の従業員 ID | E10001 |
| `status` | 文字列 | 在籍 / 退職 | 在籍 |
| `termination_date` | 日付 | 退職日 | 2026-06-15 |
| `commute_minutes` | 整数 | 通勤時間（分） | 20 |

### 勤怠（日次）（`attendance`）

出勤日・休暇取得日の 1 人 1 日 1 行。打刻漏れを含む。

- ファイル: `04_hr_attendance/attendance.csv`
- 行数: 194,821
- 主キー: `attendance_id`
- 外部キー: employee_id → employees, site_id → 05 sites

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `attendance_id` | 文字列 | 勤怠 ID | AT0000001 |
| `employee_id` | 文字列 | 従業員 ID | E10001 |
| `work_date` | 日付 | 勤務日 | 2024-11-01 |
| `site_id` | 文字列 | 勤務した拠点 | H01 |
| `work_style` | 文字列 | 出社 / テレワーク | 出社 |
| `shift_type` | 文字列 | 日勤 / 早番 / 中番 / 遅番 / 休日出勤 | 日勤 |
| `scheduled_start` | 文字列 | 所定の始業時刻 | 09:00 |
| `scheduled_end` | 文字列 | 所定の終業時刻 | 18:00 |
| `clock_in` | 日時 | 出勤打刻 | 2024-11-01 08:55:55 |
| `clock_out` | 日時 | 退勤打刻（打刻漏れは空） | 2024-11-01 18:02:51 |
| `break_minutes` | 整数 | 休憩（分） | 60 |
| `work_minutes` | 整数 | 実労働時間（分） | 487.0 |
| `overtime_minutes` | 整数 | 所定外労働（分） | 0.0 |
| `late_night_minutes` | 整数 | 深夜労働（22〜5 時、分） | 0.0 |
| `holiday_work` | 真偽 | 休日出勤か | False |
| `leave_type` | 文字列 | 休暇の種類（年次有給休暇 / 特別休暇 / 欠勤） | 年次有給休暇 |
| `note` | 文字列 | 備考 | 打刻漏れ（修正申請中） |

### 残業申請（`overtime_requests`）

正社員・契約社員の残業申請（申請理由は自由記述つき）。申請のない残業もある。

- ファイル: `04_hr_attendance/overtime_requests.csv`
- 行数: 49,852
- 主キー: `request_id`
- 外部キー: employee_id → employees, approver_employee_id → employees

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `request_id` | 文字列 | 申請 ID | OT000001 |
| `employee_id` | 文字列 | 従業員 ID | E10003 |
| `work_date` | 日付 | 対象日 | 2024-11-01 |
| `requested_minutes` | 整数 | 申請時間（分） | 90 |
| `approved_minutes` | 整数 | 承認時間（分） | 90.0 |
| `reason_category` | 文字列 | 理由区分 | 資料作成 |
| `reason_text` | 文字列 | 理由（自由記述） | 締切対応のため |
| `approver_employee_id` | 文字列 | 承認者の従業員 ID | E10001 |
| `status` | 文字列 | 承認 / 差戻し / 申請中 | 承認 |
| `requested_at` | 日時 | 申請日時 | 2024-11-01 16:32:00 |

### 研修コース（`training_courses`）

必須研修（コンプライアンス・衛生）と職種別・階層別の研修。

- ファイル: `04_hr_attendance/training_courses.csv`
- 行数: 16
- 主キー: `course_id`

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `course_id` | 文字列 | コース ID | C01 |
| `course_name` | 文字列 | コース名 | 新入社員研修 |
| `course_category` | 文字列 | 区分 | 導入研修 |
| `delivery_method` | 文字列 | 集合 / eラーニング | 集合 |
| `hours` | 整数 | 時間 | 16 |
| `mandatory` | 真偽 | 必須研修か | False |

### 研修受講（`training_records`）

研修の受講・修了記録。

- ファイル: `04_hr_attendance/training_records.csv`
- 行数: 3,986
- 主キー: `training_record_id`
- 外部キー: employee_id → employees, course_id → training_courses

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `training_record_id` | 文字列 | 受講記録 ID | TR000001 |
| `employee_id` | 文字列 | 従業員 ID | E10162 |
| `course_id` | 文字列 | コース ID | C07 |
| `enrolled_date` | 日付 | 受講（申込）日 | 2024-09-01 |
| `completed_date` | 日付 | 修了日 | 2024-09-01 |
| `status` | 文字列 | 修了 / 未修了 / 欠席 / 受講中 | 修了 |
| `score` | 整数 | テストの点数（eラーニング） | 83.0 |
| `satisfaction` | 整数 | 満足度（1〜5） | 2.0 |

### 退職者（`resignations`）

2024-11〜2026-10 の退職者。退職面談のコメント（自由記述）つき。

- ファイル: `04_hr_attendance/resignations.csv`
- 行数: 201
- 主キー: `resignation_id`
- 外部キー: employee_id → employees

| 列名 | 型 | 説明 | 例 |
|---|---|---|---|
| `resignation_id` | 文字列 | 退職 ID | RS0001 |
| `employee_id` | 文字列 | 従業員 ID | E10050 |
| `notice_date` | 日付 | 退職の申し出日 | 2024-10-02 |
| `last_working_date` | 日付 | 最終出社日（退職日） | 2024-11-06 |
| `resignation_type` | 文字列 | 自己都合 / 会社都合 / 定年 / 契約満了 | 自己都合 |
| `reason_category` | 文字列 | 退職理由の区分 | キャリアアップ |
| `exit_interview_comment` | 文字列 | 退職面談のコメント（自由記述） | 最初の数か月で教わる機会がほとんどなく、不安が大きかった。 |
| `rehire_eligible` | 真偽 | 再雇用の可否 | True |

