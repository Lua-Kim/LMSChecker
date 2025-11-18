# LMS 출결체크 프로그램 (LMSChecker)

• 	“본 코드는 저작권자의 허락 없이 사용할 수 없습니다.”
• 	“학습·연구 목적 외 사용을 금합니다.”
• 	“상업적·서비스 목적 사용 불가.”

## 1. 프로젝트 개요
이 프로젝트는 **웹 자동화 기술 학습**을 위해 제작된 프로그램입니다.  
Atosoft LMS 시스템의 출결 체크 과정을 자동화하여, 로그인과 입실/퇴실 버튼 클릭을 반복적으로 수행하는 과정을 간소화했습니다.  
실제 출석을 대체하거나 속이기 위한 목적이 아니라, **Selenium 기반 브라우저 자동화 기술을 연습**하는 데 초점을 두었습니다.

---

## 📝 주요 기능
- **자동 시간 감지**: 현재 시간을 기준으로 '입실' 또는 '퇴실' 작업을 자동으로 결정  
  - 퇴실 결정 시간: 오후 5시 50분 (`17:50`) 이후 실행 시 '퇴실'로 간주  
  - 퇴실 클릭 시간: 오후 5시 52분 (`17:52`)까지 대기 후 버튼 클릭 (서버/클라이언트 시간 오차 방지)  
- **설정 파일(`config.ini`) 기반**: 사용자 정보(이름, 비밀번호)를 코드와 분리하여 관리  
- **자동 경로 설정**: 실행 파일 위치를 기준으로 `config.ini`와 `drivers` 폴더를 자동 탐색  
- **상세 로그 기록**: 모든 동작과 오류를 `lms_checker.log`에 기록  
- **오류 처리**: 오류 발생 시 화면을 캡처(`automation_error.png`)하여 원인 파악 지원  

---

## 📂 파일 구조
```text
LMSChecker/
├── lms_checker.exe       # 실행 파일
├── config.ini            # 사용자 정보 설정 파일
└── drivers/
    └── msedgedriver.exe  # MS Edge 웹 드라이버
```

---

## ⚙️ 사용 방법
1. **`config.ini` 설정**
   ```ini
   [USER]
   Name = 사용자 이름
   Password = 비밀번호
   ```
2. **웹 드라이버 준비**
   - `drivers` 폴더에 Edge 버전에 맞는 `msedgedriver.exe` 배치  
   - Edge 버전 확인: `edge://settings/help`  
   - 드라이버 다운로드: Microsoft Edge WebDriver 공식 사이트  
3. **프로그램 실행**
   - `lms_checker.exe` 실행 → 자동 로그인 및 출결 체크 진행  
   - 완료 후 메시지 출력, Enter 키 입력 시 종료  

---

## 💻 자동화 흐름
1. 로그인 페이지 접속  
2. 사용자 정보 입력 및 로그인  
3. 출결 체크 페이지 이동  
4. 입실/퇴실 버튼 자동 클릭  
5. 성공 메시지 출력 후 종료  

---

## 🔍 코드 주요 로직
- **`get_base_path()`**: 실행 환경에 따라 기준 경로 탐색  
- **`determine_action(now)`**: 현재 시간 기준 입실/퇴실 결정  
- **`setup_driver(driver_path)`**: Selenium WebDriver 설정  
- **`perform_login(...)`**: 자동 완성 목록 활용 안정적 로그인  
- **`perform_attendance_check(...)`**: 버튼 클릭 및 Alert 처리  
- **`main()`**: 전체 흐름 제어, 예외 처리 및 오류 캡처  

---

## 🔧 문제 해결 (Troubleshooting)
- `config.ini` 파일 누락 → 실행 파일 위치 확인  
- `msedgedriver.exe` 오류 → Edge 버전 호환 여부 확인  
- 로그인/버튼 인식 실패 → UI 변경 시 CSS 선택자 수정 필요  

---

## 🛠️ 개발 정보 (HTML 분석)
```html
<input type="text" id="search" name="strSName" placeholder="수강생 이름">
<input type="password" id="strLoginPwd" name="strLoginPwd" placeholder="수강생 비밀번호">
<input type="submit" value="로그인" class="btn btn-info block full-width">
<input type="button" value="퇴실" onclick="goOutClass();">
```

---

## 📌 학습 포인트
- Selenium을 활용한 브라우저 자동화 경험  
- 반복적인 웹 작업 자동화 가능성 탐구  
- 설정 파일 관리, 로그 기록, 오류 처리 등 **실무 친화적 코드 구조** 학습  

---

• 	“본 코드는 저작권자의 허락 없이 사용할 수 없습니다.”
• 	“학습·연구 목적 외 사용을 금합니다.”
• 	“상업적·서비스 목적 사용 불가.”