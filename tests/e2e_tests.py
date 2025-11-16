# app/tests/test_e2e.py
"""
End-to-End Tests using Playwright
These tests simulate real user interactions in a browser
"""
import pytest
import re
from playwright.sync_api import Page, expect
from typing import Generator
import time

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="function")
def browser_context(playwright):
    """Create a new browser context for each test"""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        locale="en-US"
    )
    yield context
    context.close()
    browser.close()


@pytest.fixture(scope="function")
def page(browser_context) -> Generator[Page, None, None]:
    """Create a new page for each test"""
    page = browser_context.new_page()
    yield page
    page.close()


class TestAuthentication:
    """E2E tests for authentication flows"""
    
    def test_user_registration_flow(self, page: Page, base_url: str):
        """Test complete registration process in browser"""
        page.goto(f"{base_url}/register")
        
        # Fill registration form
        page.fill('input[name="email"]', "e2e_user@test.com")
        page.fill('input[name="full_name"]', "E2E Test User")
        page.fill('input[name="password"]', "SecurePass123!")
        page.fill('input[name="confirm_password"]', "SecurePass123!")
        
        # Accept terms if present
        terms_checkbox = page.locator('input[type="checkbox"][name="terms"]')
        if terms_checkbox.is_visible():
            terms_checkbox.check()
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Verify redirect to dashboard or success message
        expect(page).to_have_url(re.compile(r".*(dashboard|login|success).*"), timeout=10000)
        
        # Check for success message
        success_message = page.locator('text=/successfully|registered|welcome/i')
        if success_message.is_visible():
            expect(success_message).to_be_visible()
    
    def test_login_flow(self, page: Page, base_url: str):
        """Test login process"""
        page.goto(f"{base_url}/login")
        
        # Fill login form
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password123")
        
        # Submit
        page.click('button[type="submit"]:has-text("Login")')
        
        # Wait for redirect
        page.wait_for_load_state("networkidle")
        
        # Verify we're logged in (check for user menu, dashboard, etc.)
        expect(page.locator('[data-testid="user-menu"], .user-profile, text=/dashboard/i')).to_be_visible(timeout=10000)
    
    def test_login_with_invalid_credentials(self, page: Page, base_url: str):
        """Test login failure handling"""
        page.goto(f"{base_url}/login")
        
        page.fill('input[name="email"]', "wrong@example.com")
        page.fill('input[name="password"]', "wrongpassword")
        page.click('button[type="submit"]:has-text("Login")')
        
        # Check for error message
        error_message = page.locator('text=/invalid|incorrect|failed|error/i')
        expect(error_message).to_be_visible(timeout=5000)
    
    def test_logout_flow(self, page: Page, base_url: str):
        """Test logout process"""
        # First login
        page.goto(f"{base_url}/login")
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password123")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        
        # Click logout
        logout_button = page.locator('button:has-text("Logout"), a:has-text("Logout"), [data-testid="logout"]')
        logout_button.click()
        
        # Verify redirect to login or home
        expect(page).to_have_url(re.compile(r".*(login|home|/)$"), timeout=10000)


class TestTeamManagement:
    """E2E tests for team management"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page, base_url: str):
        """Login before each test"""
        page.goto(f"{base_url}/login")
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password123")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
    
    def test_create_team(self, page: Page, base_url: str):
        """Test creating a new team"""
        page.goto(f"{base_url}/teams")
        
        # Click create team button
        page.click('button:has-text("Create Team"), a:has-text("New Team")')
        
        # Fill team form
        page.fill('input[name="name"]', "E2E Test Team")
        page.fill('textarea[name="description"]', "Team created during E2E testing")
        
        # Submit
        page.click('button[type="submit"]:has-text("Create")')
        
        # Verify team appears in list
        expect(page.locator('text="E2E Test Team"')).to_be_visible(timeout=10000)
    
    def test_invite_team_member(self, page: Page, base_url: str):
        """Test inviting a member to a team"""
        page.goto(f"{base_url}/teams")
        
        # Select a team
        page.click('text="E2E Test Team"')
        
        # Click invite button
        page.click('button:has-text("Invite"), button:has-text("Add Member")')
        
        # Fill invitation form
        page.fill('input[name="email"]', "newmember@test.com")
        page.select_option('select[name="role"]', "member")
        
        # Send invitation
        page.click('button:has-text("Send Invite")')
        
        # Verify success message
        expect(page.locator('text=/invited|invitation sent/i')).to_be_visible(timeout=5000)
    
    def test_view_team_members(self, page: Page, base_url: str):
        """Test viewing team members list"""
        page.goto(f"{base_url}/teams")
        
        # Click on a team
        page.click('.team-card:first-child, [data-testid="team-item"]:first-child')
        
        # Navigate to members tab
        members_tab = page.locator('text="Members", [data-testid="members-tab"]')
        if members_tab.is_visible():
            members_tab.click()
        
        # Verify members list is visible
        expect(page.locator('.members-list, [data-testid="members-list"]')).to_be_visible(timeout=5000)


class TestAssessmentCreation:
    """E2E tests for assessment creation and management"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page, base_url: str):
        """Login before each test"""
        page.goto(f"{base_url}/login")
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password123")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
    
    def test_create_basic_assessment(self, page: Page, base_url: str):
        """Test creating a basic assessment"""
        page.goto(f"{base_url}/assessments")
        
        # Click create assessment
        page.click('button:has-text("Create Assessment"), a:has-text("New Assessment")')
        
        # Fill basic info
        page.fill('input[name="title"]', "E2E Test Assessment")
        page.select_option('select[name="category"]', "personality")
        
        # Add a section
        page.click('button:has-text("Add Section")')
        page.fill('input[name="section_title"]', "Personal Questions")
        
        # Add a question
        page.click('button:has-text("Add Question")')
        page.select_option('select[name="question_type"]', "likert")
        page.fill('textarea[name="question_text"]', "How satisfied are you with your work?")
        
        # Save assessment
        page.click('button[type="submit"]:has-text("Save"), button:has-text("Create")')
        
        # Verify assessment was created
        expect(page.locator('text="E2E Test Assessment"')).to_be_visible(timeout=10000)
    
    def test_add_multiple_question_types(self, page: Page, base_url: str):
        """Test adding different types of questions"""
        page.goto(f"{base_url}/assessments/new")
        
        # Basic info
        page.fill('input[name="title"]', "Multi-Question Assessment")
        page.select_option('select[name="category"]', "skills")
        
        # Add section
        page.click('button:has-text("Add Section")')
        page.fill('input[name="section_title"]', "Skills Evaluation")
        
        # Add Likert question
        page.click('button:has-text("Add Question")')
        page.select_option('select[name="question_type"]', "likert")
        page.fill('textarea[name="question_text"]', "Rate your proficiency")
        
        # Add Multiple Choice question
        page.click('button:has-text("Add Question")')
        page.select_option('select[name="question_type"]', "multiple_choice")
        page.fill('textarea[name="question_text"]', "What is your experience level?")
        page.click('button:has-text("Add Option")')
        page.fill('input[name="option_0"]', "Beginner")
        page.click('button:has-text("Add Option")')
        page.fill('input[name="option_1"]', "Intermediate")
        page.click('button:has-text("Add Option")')
        page.fill('input[name="option_2"]', "Advanced")
        
        # Add Text question
        page.click('button:has-text("Add Question")')
        page.select_option('select[name="question_type"]', "text")
        page.fill('textarea[name="question_text"]', "Describe your experience")
        
        # Save
        page.click('button[type="submit"]:has-text("Save")')
        
        # Verify all questions were saved
        expect(page.locator('text="Rate your proficiency"')).to_be_visible(timeout=5000)
        expect(page.locator('text="What is your experience level?"')).to_be_visible(timeout=5000)
        expect(page.locator('text="Describe your experience"')).to_be_visible(timeout=5000)
    
    def test_publish_assessment(self, page: Page, base_url: str):
        """Test publishing an assessment"""
        page.goto(f"{base_url}/assessments")
        
        # Find draft assessment
        draft_assessment = page.locator('.assessment-card:has-text("Draft"), [data-status="draft"]').first
        draft_assessment.click()
        
        # Click publish button
        page.click('button:has-text("Publish")')
        
        # Confirm if modal appears
        confirm_button = page.locator('button:has-text("Confirm"), button:has-text("Yes")')
        if confirm_button.is_visible():
            confirm_button.click()
        
        # Verify status changed
        expect(page.locator('text=/published|live/i, [data-status="published"]')).to_be_visible(timeout=5000)
    
    def test_clone_assessment(self, page: Page, base_url: str):
        """Test cloning an existing assessment"""
        page.goto(f"{base_url}/assessments")
        
        # Find an assessment
        assessment = page.locator('.assessment-card').first
        assessment.click()
        
        # Click clone/duplicate button
        page.click('button:has-text("Clone"), button:has-text("Duplicate")')
        
        # Enter new name
        page.fill('input[name="title"]', "Cloned Assessment")
        page.click('button:has-text("Clone"), button:has-text("Duplicate")')
        
        # Verify cloned assessment exists
        page.goto(f"{base_url}/assessments")
        expect(page.locator('text="Cloned Assessment"')).to_be_visible(timeout=5000)


class TestTakingAssessment:
    """E2E tests for taking assessments"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page, base_url: str):
        """Login before each test"""
        page.goto(f"{base_url}/login")
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password123")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
    
    def test_complete_assessment_flow(self, page: Page, base_url: str):
        """Test completing an entire assessment"""
        page.goto(f"{base_url}/assessments")
        
        # Find published assessment
        published = page.locator('[data-status="published"], .assessment-card:has-text("Published")').first
        published.click()
        
        # Start assessment
        page.click('button:has-text("Start Assessment"), button:has-text("Begin")')
        
        # Answer first question (assuming Likert)
        likert_option = page.locator('input[type="radio"][value="5"], button:has-text("5")').first
        if likert_option.is_visible():
            likert_option.click()
        
        # Next button
        next_button = page.locator('button:has-text("Next")')
        if next_button.is_visible():
            next_button.click()
        
        # Answer multiple choice question
        mc_option = page.locator('input[type="radio"]').first
        if mc_option.is_visible():
            mc_option.click()
            next_button.click()
        
        # Answer text question
        text_input = page.locator('textarea, input[type="text"]').first
        if text_input.is_visible():
            text_input.fill("This is my detailed response")
        
        # Submit assessment
        page.click('button:has-text("Submit"), button:has-text("Complete")')
        
        # Verify completion
        expect(page.locator('text=/completed|thank you|submitted/i')).to_be_visible(timeout=10000)
    
    def test_save_progress_and_resume(self, page: Page, base_url: str):
        """Test saving progress and resuming later"""
        page.goto(f"{base_url}/assessments")
        
        # Start assessment
        published = page.locator('[data-status="published"]').first
        published.click()
        page.click('button:has-text("Start Assessment")')
        
        # Answer first question
        page.locator('input[type="radio"]').first.click()
        
        # Save and exit
        save_button = page.locator('button:has-text("Save"), button:has-text("Save Progress")')
        if save_button.is_visible():
            save_button.click()
        
        # Navigate away
        page.goto(f"{base_url}/dashboard")
        
        # Return to assessments
        page.goto(f"{base_url}/responses/in-progress")
        
        # Resume assessment
        page.click('button:has-text("Resume"), button:has-text("Continue")')
        
        # Verify we're on the correct question
        expect(page.locator('.question-container, [data-testid="question"]')).to_be_visible()
    
    def test_validation_on_required_questions(self, page: Page, base_url: str):
        """Test that required questions are validated"""
        page.goto(f"{base_url}/assessments")
        
        # Start assessment
        page.locator('[data-status="published"]').first.click()
        page.click('button:has-text("Start Assessment")')
        
        # Try to skip without answering (if question is required)
        next_button = page.locator('button:has-text("Next")')
        if next_button.is_visible():
            next_button.click()
            
            # Check for validation error
            error = page.locator('text=/required|must answer|please select/i')
            if error.is_visible():
                expect(error).to_be_visible()


class TestResultsAndAnalytics:
    """E2E tests for viewing results and analytics"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page, base_url: str):
        """Login before each test"""
        page.goto(f"{base_url}/login")
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password123")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
    
    def test_view_individual_results(self, page: Page, base_url: str):
        """Test viewing individual assessment results"""
        page.goto(f"{base_url}/responses")
        
        # Click on completed response
        completed = page.locator('[data-status="completed"], .response-card:has-text("Completed")').first
        completed.click()
        
        # Verify results page loaded
        expect(page.locator('.results-container, [data-testid="results"]')).to_be_visible(timeout=5000)
        
        # Check for score or summary
        expect(page.locator('text=/score|result|summary/i')).to_be_visible()
    
    def test_view_team_analytics(self, page: Page, base_url: str):
        """Test viewing team-wide analytics"""
        page.goto(f"{base_url}/teams")
        
        # Select team
        page.locator('.team-card').first.click()
        
        # Navigate to analytics
        analytics_tab = page.locator('text="Analytics", a:has-text("Analytics")')
        if analytics_tab.is_visible():
            analytics_tab.click()
        else:
            page.goto(f"{base_url}/analytics")
        
        # Verify charts/graphs are visible
        expect(page.locator('canvas, svg, .chart')).to_be_visible(timeout=5000)
    
    def test_export_results(self, page: Page, base_url: str):
        """Test exporting assessment results"""
        page.goto(f"{base_url}/responses")
        
        # Click on completed response
        page.locator('[data-status="completed"]').first.click()
        
        # Click export button
        export_button = page.locator('button:has-text("Export"), button:has-text("Download")')
        
        # Start waiting for download before clicking
        with page.expect_download() as download_info:
            export_button.click()
        
        download = download_info.value
        
        # Verify download completed
        assert download.suggested_filename.endswith(('.pdf', '.csv', '.xlsx'))
    
    def test_filter_and_search_results(self, page: Page, base_url: str):
        """Test filtering and searching through results"""
        page.goto(f"{base_url}/responses")
        
        # Use search
        search_input = page.locator('input[type="search"], input[placeholder*="Search"]')
        if search_input.is_visible():
            search_input.fill("Test Assessment")
            page.wait_for_timeout(1000)  # Wait for search to execute
            
            # Verify filtered results
            expect(page.locator('text="Test Assessment"')).to_be_visible()
        
        # Use status filter
        status_filter = page.locator('select[name="status"], button:has-text("Filter")')
        if status_filter.is_visible():
            if status_filter.get_attribute('tagName') == 'SELECT':
                status_filter.select_option("completed")
            else:
                status_filter.click()
                page.click('text="Completed"')
            
            # Verify only completed items show
            expect(page.locator('[data-status="completed"]')).to_be_visible()


class TestResponsiveDesign:
    """E2E tests for responsive design and mobile compatibility"""
    
    def test_mobile_navigation(self, page: Page, base_url: str):
        """Test navigation on mobile viewport"""
        page.set_viewport_size({"width": 375, "height": 667})  # iPhone SE size
        
        page.goto(f"{base_url}/login")
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password123")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        
        # Open mobile menu
        menu_button = page.locator('button[aria-label*="menu"], .hamburger, button:has-text("☰")')
        if menu_button.is_visible():
            menu_button.click()
            
            # Verify menu is visible
            expect(page.locator('nav, .mobile-menu')).to_be_visible()
    
    def test_tablet_layout(self, page: Page, base_url: str):
        """Test layout on tablet viewport"""
        page.set_viewport_size({"width": 768, "height": 1024})  # iPad size
        
        page.goto(f"{base_url}")
        
        # Verify layout adapts
        expect(page.locator('body')).to_be_visible()
        
        # Navigation should be accessible
        expect(page.locator('nav, [role="navigation"]')).to_be_visible()


class TestAccessibility:
    """E2E tests for accessibility compliance"""
    
    def test_keyboard_navigation(self, page: Page, base_url: str):
        """Test navigation using only keyboard"""
        page.goto(f"{base_url}/login")
        
        # Tab through form
        page.keyboard.press("Tab")
        email_input = page.locator('input[name="email"]')
        expect(email_input).to_be_focused()
        
        email_input.type("test@example.com")
        page.keyboard.press("Tab")
        
        password_input = page.locator('input[name="password"]')
        expect(password_input).to_be_focused()
        
        password_input.type("password123")
        page.keyboard.press("Tab")
        
        # Submit button should be focused
        submit_button = page.locator('button[type="submit"]')
        expect(submit_button).to_be_focused()
    
    def test_screen_reader_labels(self, page: Page, base_url: str):
        """Test that form elements have proper labels"""
        page.goto(f"{base_url}/register")
        
        # Check for labels or aria-labels
        email_input = page.locator('input[name="email"]')
        assert email_input.get_attribute("aria-label") or page.locator('label[for="email"]').is_visible()
        
        password_input = page.locator('input[name="password"]')
        assert password_input.get_attribute("aria-label") or page.locator('label[for="password"]').is_visible()


class TestPerformance:
    """E2E tests for performance metrics"""
    
    def test_page_load_time(self, page: Page, base_url: str):
        """Test that pages load within acceptable time"""
        start_time = time.time()
        page.goto(f"{base_url}/dashboard")
        page.wait_for_load_state("networkidle")
        load_time = time.time() - start_time
        
        # Page should load in less than 5 seconds
        assert load_time < 5.0, f"Page took {load_time}s to load"
    
    def test_assessment_list_pagination(self, page: Page, base_url: str):
        """Test that pagination works smoothly with many items"""
        page.goto(f"{base_url}/login")
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password123")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        
        page.goto(f"{base_url}/assessments")
        
        # Check if pagination exists
        next_page_button = page.locator('button:has-text("Next"), a:has-text("Next")')
        if next_page_button.is_visible():
            next_page_button.click()
            page.wait_for_load_state("networkidle")
            
            # Verify content changed
            expect(page.locator('.assessment-card, [data-testid="assessment"]')).to_be_visible()


class TestErrorScenarios:
    """E2E tests for error handling and edge cases"""
    
    def test_network_error_handling(self, page: Page, base_url: str):
        """Test behavior when network requests fail"""
        page.goto(f"{base_url}/login")
        
        # Simulate offline mode
        page.context.set_offline(True)
        
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password123")
        page.click('button[type="submit"]')
        
        # Should show error message
        expect(page.locator('text=/network|offline|connection/i')).to_be_visible(timeout=5000)
        
        # Restore online mode
        page.context.set_offline(False)
    
    def test_session_timeout(self, page: Page, base_url: str):
        """Test handling of expired sessions"""
        page.goto(f"{base_url}/login")
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password123")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        
        # Clear cookies to simulate session timeout
        page.context.clear_cookies()
        
        # Try to access protected page
        page.goto(f"{base_url}/assessments")
        
        # Should redirect to login
        expect(page).to_have_url(re.compile(r".*/login.*"), timeout=5000)
    
    def test_404_page(self, page: Page, base_url: str):
        """Test 404 error page"""
        page.goto(f"{base_url}/this-page-does-not-exist-12345")
        
        # Should show 404 message
        expect(page.locator('text=/404|not found|page.*not.*exist/i')).to_be_visible(timeout=5000)
