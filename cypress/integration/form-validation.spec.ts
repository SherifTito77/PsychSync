import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps';

// Feature: User Registration Form Validation

Given('I am on the registration page', () => {
  cy.visit('/register');
});

When('I submit the form with empty required fields', () => {
  cy.get('[data-testid="register-form"]').submit();
});

Then('I should see validation errors for required fields', () => {
  cy.get('[data-testid="email-error"]')
    .should('be.visible')
    .and('contain', 'Email is required');

  cy.get('[data-testid="password-error"]')
    .should('be.visible')
    .and('contain', 'Password is required');

  cy.get('[data-testid="name-error"]')
    .should('be.visible')
    .and('contain', 'Name is required');
});

When('I enter an invalid email format', () => {
  cy.get('[data-testid="email-input"]').type('invalid-email');
  cy.get('[data-testid="register-form"]').submit();
});

Then('I should see email format validation error', () => {
  cy.get('[data-testid="email-error"]')
    .should('be.visible')
    .and('contain', 'Please enter a valid email address');
});

When('I enter a password that is too short', () => {
  cy.get('[data-testid="email-input"]').type('test@example.com');
  cy.get('[data-testid="password-input"]').type('123');
  cy.get('[data-testid="register-form"]').submit();
});

Then('I should see password length validation error', () => {
  cy.get('[data-testid="password-error"]')
    .should('be.visible')
    .and('contain', 'Password must be at least 8 characters');
});

// Assessment Form Validation
Given('I am taking an assessment', () => {
  cy.login('test@example.com', 'password');
  cy.visit('/assessments/mbti');
});

When('I try to submit without answering all questions', () => {
  cy.get('[data-testid="submit-assessment"]').click();
});

Then('I should see incomplete assessment warning', () => {
  cy.get('[data-testid="incomplete-warning"]')
    .should('be.visible')
    .and('contain', 'Please answer all questions before submitting');
});

// API Validation
describe('Form Validation API Tests', () => {
  it('should validate registration data', () => {
    cy.request({
      method: 'POST',
      url: '/api/v1/auth/register',
      body: {
        email: 'invalid-email',
        password: '123',
        full_name: 'Test User'
      },
      failOnStatusCode: false
    }).then((response) => {
      expect(response.status).to.equal(422);
      expect(response.body).to.have.property('detail');
      expect(response.body.detail).to.be.an('array');
    });
  });

  it('should validate assessment submission', () => {
    cy.login('test@example.com', 'password');
    cy.request({
      method: 'POST',
      url: '/api/v1/assessments/mbti/submit',
      body: {
        responses: [] // Empty responses
      },
      failOnStatusCode: false
    }).then((response) => {
      expect(response.status).to.equal(400);
      expect(response.body).to.have.property('detail');
    });
  });
});

// Visual Regression Tests
describe('Form Visual Validation', () => {
  it('should look correct on different screen sizes', () => {
    ['iphone-6', 'ipad-2', 'macbook-13'].forEach(device => {
      cy.viewport(device);
      cy.visit('/register');
      cy.get('[data-testid="register-form"]').should('be.visible');
      cy.matchImageSnapshot(`registration-form-${device}`);
    });
  });
});
