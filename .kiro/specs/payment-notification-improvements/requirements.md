# Requirements Document

## Introduction

This feature enhances the payment notification system in the HashSlash School Bot to improve administrator workflow by including buyer usernames in payment notifications and preventing deletion of approved payment messages. This will allow administrators to directly contact buyers without relying on message forwarding, which can hide usernames, and maintain a record of approved payments.

## Requirements

### Requirement 1

**User Story:** As an administrator, I want to see the buyer's username in payment notifications, so that I can directly contact them without having to rely on forwarded messages that may hide usernames.

#### Acceptance Criteria

1. WHEN a payment receipt is submitted THEN the system SHALL include the buyer's Telegram username in the payment notification message sent to the admin chat
2. WHEN a buyer has no username set THEN the system SHALL include their first name and last name instead
3. WHEN a buyer has neither username nor full name THEN the system SHALL include their Telegram user ID as fallback identification
4. WHEN the payment notification is sent THEN the username/name SHALL be clearly labeled and easily identifiable in the message format

### Requirement 2

**User Story:** As an administrator, I want approved payment messages to remain in the chat, so that I can maintain a record of processed payments and reference them later if needed.

#### Acceptance Criteria

1. WHEN an administrator approves a payment THEN the system SHALL NOT delete the original payment notification message
2. WHEN an administrator approves a payment THEN the system SHALL update the message to indicate approval status
3. WHEN an administrator rejects a payment THEN the system SHALL still delete the message as before
4. WHEN a payment is approved THEN the updated message SHALL clearly show the approval status and timestamp
5. WHEN viewing approved payments THEN administrators SHALL be able to distinguish between approved and pending payments in the chat history