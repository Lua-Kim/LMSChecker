import os
import time
import datetime
import sys
import configparser
from selenium.webdriver.edge.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.edge.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC


# --- 설정 (Constants) ---
LOGIN_URL = "https://microsoft.atosoft.net/worknet/Slogin.asp"
WAIT_TIMEOUT = 10
CHECKOUT_DECISION_TIME = datetime.time(17, 50) # 퇴실을 결정하는 시간
CHECKOUT_CLICK_TIME_H = 17 # 퇴실을 클릭하는 시간 (시)
CHECKOUT_CLICK_TIME_M = 52 # 퇴실을 클릭하는 시간 (분)

# --- Selectors (CSS 선택자 및 XPath) ---
SEARCH_INPUT_ID = "search"
PASSWORD_INPUT_ID = "strLoginPwd"
LOGIN_BUTTON_SELECTOR = "input[value='로그인']"
ATTENDANCE_LINK_TEXT = "출결체크"

def get_base_path():
    """PyInstaller로 패키징되었을 때와 직접 실행할 때 모두 올바른 경로를 반환합니다."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def load_config():
    """설정 파일(config.ini)을 읽어 사용자 정보와 설정을 반환합니다."""
    print("[DEBUG] config.ini 로드 시도")
    config = configparser.ConfigParser()
    config_path = os.path.join(get_base_path(), 'config.ini')
    print(f"[DEBUG] config.ini 경로: {config_path}")
    if not config.read(config_path, encoding='utf-8'):
        print("❌ 오류: 설정 파일(config.ini)을 찾을 수 없습니다.")
        input("Enter 키를 눌러 종료...")
        return None
    print("[DEBUG] config.ini 로드 성공")
    return config

class Logger:
    """stdout과 stderr를 파일과 콘솔에 동시에 출력하는 로거"""
    def __init__(self, filename="lms_checker.log"):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        log_path = os.path.join(get_base_path(), filename)
        print(f"[DEBUG] 로그 파일 경로: {log_path}")
        self.logfile = open(log_path, 'a', encoding='utf-8')

    def write(self, message):
        self.original_stdout.write(message)
        if message.strip():
            self.logfile.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message.strip()}\n")
        self.flush()

    def flush(self):
        self.original_stdout.flush()
        self.logfile.flush()

    def close(self):
        self.logfile.close()
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

def determine_action(now):
    """현재 시간에 따라 '입실' 또는 '퇴실'을 결정합니다."""
    print(f"[DEBUG] 현재 시간: {now.strftime('%H:%M:%S')}")
    if now.time() >= CHECKOUT_DECISION_TIME:
        return "퇴실"
    return "입실"

def setup_driver(driver_path):
    """Selenium WebDriver를 설정하고 반환합니다."""
    print(f"[DEBUG] WebDriver 경로: {driver_path}")
    if not os.path.isfile(driver_path):
        print(f"❌ 오류: msedgedriver.exe를 찾을 수 없습니다: {driver_path}")
        input("Enter 키를 눌러 종료...")
        raise FileNotFoundError(f"msedgedriver.exe not found at: {driver_path}")
    edge_options = Options()
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option("useAutomationExtension", False)
    edge_options.add_experimental_option("detach", True)
    service = Service(executable_path=driver_path)
    print("[DEBUG] WebDriver 초기화 시도")
    driver = webdriver.Edge(service=service, options=edge_options)
    print("[DEBUG] WebDriver 초기화 성공")
    return driver

def perform_login(driver, wait, name, password):
    """로그인 페이지로 이동하여 로그인을 수행합니다."""
    print("\n[2/5] 로그인 페이지로 이동 및 로그인 시도...")
    driver.get(LOGIN_URL)
    
    search_input = wait.until(EC.visibility_of_element_located((By.ID, SEARCH_INPUT_ID)))
    search_input.send_keys(name)
    
    autocomplete_xpath = f"//ul[contains(@class, 'ui-autocomplete')]//*[contains(text(), '{name}')]"
    autocomplete_item = wait.until(EC.visibility_of_element_located((By.XPATH, autocomplete_xpath)))
    autocomplete_item.click()
    print(f"'{name}' 님을 자동 완성 목록에서 선택했습니다.")
    
    driver.find_element(By.ID, PASSWORD_INPUT_ID).send_keys(password)
    # 자동 완성 선택 후 페이지 내부 스크립트가 안정화될 시간을 줍니다.
    time.sleep(0.5) 

    login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, LOGIN_BUTTON_SELECTOR)))
    login_button.click()
    print("로그인 버튼을 클릭했습니다. 다음 페이지 로드를 기다립니다...")

def navigate_to_attendance_page(driver, wait):
    """출결체크 페이지로 이동하고 새 탭으로 전환합니다."""
    print("\n[3/5] 출결체크 페이지로 이동합니다...")
    original_window = driver.current_window_handle
    
    check_page_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, ATTENDANCE_LINK_TEXT)))
    check_page_link.click()
    print("'출결체크' 링크를 클릭하여 새 탭으로 이동합니다.")

    wait.until(EC.number_of_windows_to_be(2))
    for window_handle in driver.window_handles:
        if window_handle != original_window:
            driver.switch_to.window(window_handle)
            break
    print("새 탭(출결 페이지)으로 제어권을 전환했습니다.")

def perform_attendance_check(driver, wait, action_text, now):
    """최종 입실 또는 퇴실 버튼을 클릭하고 알림 창을 처리합니다."""
    if action_text == "퇴실":
        checkout_click_time = now.replace(hour=CHECKOUT_CLICK_TIME_H, minute=CHECKOUT_CLICK_TIME_M, second=0, microsecond=0)
        if now < checkout_click_time:
            wait_seconds = (checkout_click_time - now).total_seconds()
            print(f"퇴실 클릭 시간({checkout_click_time.strftime('%H:%M:%S')})까지 약 {int(wait_seconds)}초 동안 대기합니다...")
            time.sleep(wait_seconds)
            print("대기 완료. 퇴실 처리를 계속합니다.")

    completed_button_selector = f"input[value^='{action_text}시간']"
    try:
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, completed_button_selector)))
        print(f"\n[정보] '{action_text}시간' 버튼이 확인되었습니다. 이미 처리가 완료된 것 같습니다.")
        return
    except TimeoutException:
        pass

    print(f"\n[4/5] '{action_text}' 버튼을 찾아 클릭을 시도합니다...")
    button_selector = f"input[value='{action_text}']"
    final_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))
    final_button.click()
    print(f"'{action_text}' 버튼을 클릭했습니다.")

    if action_text == "퇴실":
        print("퇴실 확인 메시지 창을 확인합니다...")
        try:
            alert = wait.until(EC.alert_is_present(), message="퇴실 확인 알림 창이 나타나지 않았습니다.")
            alert_text = alert.text
            print(f"알림 창이 나타났습니다: '{alert_text}'")
            alert.accept()
            print("알림 창의 '확인' 버튼을 클릭했습니다.")
        except TimeoutException:
            print("경고: 퇴실 확인 알림 창이 예상과 달리 나타나지 않았습니다. (HTML 모달일 수 있습니다)")
        except Exception as alert_e:
            print(f"알림 창 처리 중 예상치 못한 오류 발생: {alert_e}")

def main():
    """메인 실행 함수: 브라우저를 실행하고 출석 체크 자동화를 수행합니다."""
    print("[DEBUG] main() 함수 진입")
    driver = None
    try:
        config = load_config()
        if not config:
            return
        print("[DEBUG] config 로드 성공")

        STUDENT_NAME = config.get('USER', 'Name')
        STUDENT_PASSWORD = config.get('USER', 'Password')
        # config.ini에서 경로를 읽는 대신, 'drivers' 폴더로 경로를 고정합니다.
        DRIVER_PATH = os.path.join(get_base_path(), "drivers", "msedgedriver.exe")
        print(f"[DEBUG] DRIVER_PATH: {DRIVER_PATH}")

        print("[DEBUG] 드라이버 파일 존재 확인 완료")

        now = datetime.datetime.now()
        action_text = determine_action(now)
        print(f"▶ 자동 {action_text} 체크를 시작합니다... (현재 시간: {now.strftime('%H:%M:%S')})")
        
        driver = setup_driver(DRIVER_PATH)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)

        perform_login(driver, wait, STUDENT_NAME, STUDENT_PASSWORD)

        try:
            print("\n[3/5] 출결 페이지 확인 중...")
            short_wait = WebDriverWait(driver, 1)
            short_wait.until(EC.presence_of_element_located((By.LINK_TEXT, ATTENDANCE_LINK_TEXT)))
            print("'출결체크' 링크를 발견했습니다. 페이지를 이동합니다.")
            navigate_to_attendance_page(driver, wait)
        except TimeoutException:
            print("바로 출석 페이지로 이동한 것을 확인했습니다. 다음 단계를 계속 진행합니다.")

        perform_attendance_check(driver, wait, action_text, now)
        
        print(f"\n🎉 성공: 모든 {action_text} 체크 과정이 완료되었습니다!")
        input("작업 완료. Enter 키를 눌러 종료...")

    except BaseException as e:
        import traceback
        print(f"\n❌ 오류 발생: {type(e).__name__} - {str(e)}")
        traceback.print_exc()
        input("오류 확인 후 Enter 키를 눌러 종료...")
        try:
            if driver:
                screenshot_path = os.path.join(get_base_path(), "automation_error.png")
                driver.save_screenshot(screenshot_path)
                print(f"오류 화면을 '{screenshot_path}' 파일로 저장했습니다.")
        except:
            print("스크린샷 저장에 실패했습니다. (드라이버가 실행되지 않았을 수 있습니다)")
    finally:
        if driver:
            # input("\n[완료] 자동화 작업이 끝났습니다. 브라우저를 닫으려면 Enter 키를 누르세요...")
            print("\n[완료] 자동화 작업이 끝났습니다.")
            time.sleep(5)
            input("Enter 키를 눌러 종료...")
            driver.quit() # quit()은 브라우저와 드라이버 프로세스를 모두 종료합니다.

if __name__ == "__main__":
    print("[DEBUG] 프로그램 시작: Logger 초기화 전")
    try:
        logger = Logger()
        sys.stdout = logger
        sys.stderr = logger
        print("="*50)
        print(f"LMS 자동 출석체크 프로그램을 시작합니다. (실행 시각: {datetime.datetime.now()})")
        main()
        print("="*50 + "\n")
        logger.close()
    except BaseException as e:
        print(f"[DEBUG] 최상위 오류 발생: {type(e).__name__} - {str(e)}")
        import traceback
        traceback.print_exc()
        with open("critical_error.log", "w", encoding="utf-8") as f:
            f.write(f"A critical error occurred: {type(e).__name__}\n")
            f.write(str(e) + "\n")
            traceback.print_exc(file=f)
        input("[DEBUG] 최상위 오류 확인 후 Enter 키를 눌러 종료...")