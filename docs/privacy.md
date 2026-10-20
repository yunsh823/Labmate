# ToDoList 개인정보처리방침 / Privacy Policy

시행일: 2026년 10월 20일 · Effective: October 20, 2026

[한국어](#한국어) · [English](#english)

---

## 한국어

ToDoList(이하 "앱")는 Windows용 개인 할 일 관리 프로그램입니다. 이 방침은 앱이 어떤 정보를 어디에 저장하고, 어떤 외부 서비스와 주고받는지 설명합니다.

### 1. 기본 원칙

- 앱의 모든 데이터는 **사용자의 컴퓨터에만** 저장됩니다.
- 개발자는 별도의 서버를 운영하지 않으며, 사용자의 데이터를 받거나 보관하지 않습니다.
- 사용 통계, 광고, 추적 기능은 없습니다.
- 아래 외부 서비스와의 통신은 사용자가 해당 기능을 직접 켜거나 설정했을 때만 일어납니다.

### 2. 컴퓨터에 저장되는 정보

모든 파일은 `%APPDATA%\ToDoList\` 폴더에 저장됩니다.

| 파일 | 내용 |
|---|---|
| `todo.db` | 할 일, 프로젝트, 마감일, 메모, 앱 설정(테마·언어·글꼴 등), 기상청 API 키, 날씨 위치(동네 이름과 격자 번호), 논문 알림 설정(기준 논문 DOI·키워드·저널), 받은 논문 목록 |
| `google_token.json` | 구글 캘린더를 연결한 경우 발급되는 로그인 정보(액세스·리프레시 토큰) |
| `client_secret.json` | 사용자가 직접 가져온 구글 OAuth 클라이언트 파일(가져온 경우에만) |

- 이 파일들은 암호화되지 않은 상태로 저장되므로, 컴퓨터 계정 보안은 사용자가 관리해야 합니다.
- 앱을 삭제해도 이 폴더는 남습니다. 완전히 지우려면 폴더를 직접 삭제하세요.
- "Windows 시작 시 자동 실행"을 켜면 Windows 레지스트리(`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`)에 앱 실행 경로가 등록되고, 끄거나 앱을 삭제하면 지워집니다.

### 3. 외부 서비스와 주고받는 정보

#### 3-1. 구글 캘린더 (사용자가 "연결"한 경우)

- **요청 권한**
  - `https://www.googleapis.com/auth/calendar.readonly`: 캘린더 목록과 일정을 읽어, 오늘의 일정을 앱에 보여 주기 위해 사용합니다.
  - `https://www.googleapis.com/auth/calendar.events`: 날짜와 시간이 있는 할 일을 사용자의 기본 캘린더에 일정으로 만들고, 수정·삭제하기 위해 사용합니다.
- **사용 방식**
  - 앱은 오늘 날짜의 일정(제목, 시작·종료 시각, 캘린더 이름과 색)을 읽어 화면에 표시합니다. 이 정보는 메모리에만 두고 디스크에 저장하지 않습니다.
  - 시간이 있는 할 일은 제목과 날짜·시간으로 일정을 만들고, 앱이 만든 일정임을 표시하는 값을 함께 저장합니다.
  - 앱이 만든 일정이 캘린더에서 수정되면 할 일에 반영하고, 삭제되면 해당 할 일을 휴지통으로 옮깁니다.
- 구글에서 받은 정보는 위 기능에만 사용하며, 개발자를 포함한 누구에게도 전송·판매·공유하지 않고, 광고나 AI 모델 학습에 사용하지 않습니다.
- ToDoList가 Google API에서 받은 정보를 사용하고 다른 앱으로 전송하는 방식은 [Google API 서비스 사용자 데이터 정책](https://developers.google.com/terms/api-services-user-data-policy)의 제한적 사용(Limited Use) 요구사항을 포함하여 해당 정책을 준수합니다.
- 설정에서 "연결 해제"를 누르면 컴퓨터에 저장된 로그인 정보가 삭제됩니다. 구글 계정 쪽 권한까지 철회하려면 [Google 계정의 서드 파티 연결 관리](https://myaccount.google.com/connections)에서 ToDoList를 삭제하세요.

#### 3-2. 기상청 API 허브 (날씨 기능을 설정한 경우)

- 사용자가 입력한 기상청 API 키와 선택한 동네의 **기상청 격자 번호**(약 5km 단위), 예보 기준 시각을 기상청 API 허브(`apihub.kma.go.kr`)로 보냅니다.
- 정확한 주소나 GPS 위치는 보내지 않습니다.

#### 3-3. 논문 알림 (기준 논문·키워드·저널을 설정한 경우)

- **Semantic Scholar**(`api.semanticscholar.org`): 사용자가 등록한 기준 논문의 DOI를 보내 관련 논문을 추천받습니다.
- **OpenAlex**(`api.openalex.org`): 사용자가 등록한 키워드, 저널 식별자, 검색 기간을 보내 최근 논문을 찾습니다. 기준 논문을 추가할 때는 논문 제목을 확인하기 위해 해당 DOI를, 설정에서 저널을 검색할 때는 입력한 저널 이름을 보냅니다.
- 이름, 이메일 등 사용자를 식별할 수 있는 정보는 보내지 않습니다.

#### 3-4. 그 밖의 통신

- 논문 제목을 누르면 기본 웹 브라우저에서 해당 논문 페이지(DOI 주소)가 열립니다.
- 앱이 두 번 실행되지 않도록 하는 통신은 사용자의 컴퓨터 안(`127.0.0.1`)에서만 이루어집니다.

각 외부 서비스는 자체 개인정보처리방침에 따라 요청을 처리합니다.

### 4. 아동

앱은 아동을 대상으로 하지 않으며, 아동의 정보를 의도적으로 수집하지 않습니다.

### 5. 방침 변경

방침이 바뀌면 이 문서를 수정하고 상단의 시행일을 갱신합니다.

### 6. 문의

이 프로젝트의 GitHub 저장소 Issues 페이지로 문의해 주세요.

---

## English

ToDoList ("the app") is a personal to-do app for Windows. This policy explains what the app stores, where it stores it, and what it exchanges with outside services.

### 1. Principles

- All app data is stored **only on your computer**.
- The developer runs no server and never receives or keeps your data.
- There is no analytics, advertising, or tracking.
- The app contacts the services below only when you turn on or configure the related feature.

### 2. Data stored on your computer

All files are kept in `%APPDATA%\ToDoList\`.

| File | Contents |
|---|---|
| `todo.db` | Tasks, projects, due dates, notes, app settings (theme, language, font, etc.), your KMA API key, weather location (neighbourhood name and grid number), paper-alert settings (seed DOIs, keywords, journals), and fetched papers |
| `google_token.json` | Sign-in credentials (access and refresh tokens) issued when you connect Google Calendar |
| `client_secret.json` | A Google OAuth client file you imported yourself (only if you did) |

- These files are not encrypted; protecting your computer account is up to you.
- Uninstalling the app leaves this folder in place. Delete it to remove all data.
- If you turn on "Start with Windows", the app's path is added to `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`; it is removed when you turn it off or uninstall.

### 3. Data exchanged with outside services

#### 3.1 Google Calendar (only if you click "Connect")

- **Scopes requested**
  - `https://www.googleapis.com/auth/calendar.readonly`: to read your calendar list and events so today's events can be shown in the app.
  - `https://www.googleapis.com/auth/calendar.events`: to create, update, and delete events on your primary calendar for tasks that have a date and time.
- **How the data is used**
  - The app reads today's events (title, start and end time, calendar name and color) and displays them. This is kept in memory only and never written to disk.
  - For a task with a time, the app creates an event with the task's title, date, and time, plus a private marker identifying it as created by the app.
  - When such an event is changed in Google Calendar, the change is applied to the task; when it is deleted, the task moves to the app's trash.
- Data received from Google is used only for the features above. It is never transferred, sold, or shared with anyone, including the developer, and is never used for advertising or to train AI models.
- ToDoList's use and transfer of information received from Google APIs to any other app will adhere to the [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy), including the Limited Use requirements.
- "Disconnect" in Settings deletes the stored credentials. To revoke the app's access on Google's side as well, remove ToDoList at [Third-party connections in your Google Account](https://myaccount.google.com/connections).

#### 3.2 KMA API Hub (only if you set up weather)

- The app sends your KMA API key, the **KMA forecast grid number** of the neighbourhood you chose (about 5 km resolution), and the forecast base time to the Korea Meteorological Administration API Hub (`apihub.kma.go.kr`).
- No street address or GPS location is sent.

#### 3.3 Paper alerts (only if you add seed papers, keywords, or journals)

- **Semantic Scholar** (`api.semanticscholar.org`): the DOIs of your seed papers, to get related recommendations.
- **OpenAlex** (`api.openalex.org`): your keywords, journal identifiers, and the search period, to find recent papers; a seed paper's DOI when you add it, to look up its title; and the journal name you type when searching for a journal in Settings.
- Nothing that identifies you, such as your name or email, is sent.

#### 3.4 Other connections

- Clicking a paper title opens its page (its DOI link) in your default web browser.
- The check that keeps the app from running twice talks only to your own computer (`127.0.0.1`).

Each outside service handles requests under its own privacy policy.

### 4. Children

The app is not directed at children and does not knowingly collect children's information.

### 5. Changes

If this policy changes, this page will be updated along with the effective date above.

### 6. Contact

Please open an issue on this project's GitHub repository.
