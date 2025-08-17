# Implementation Plan

- [ ] 1. Create utility functions for enhanced user identification and course flow information
  - Add `get_user_identification()` function to extract username, name, or user ID with proper formatting
  - Add `get_course_flow_info()` function to format course flow number and start date information
  - Add these functions to `utils.py` module for reusability across handlers
  - Write unit tests for both utility functions to verify correct identification priority and formatting
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 2. Update photo handler admin notification format
  - Modify `photo_handler()` in `handlers/message_handlers.py` to use enhanced user identification
  - Update admin notification message format to include course flow information using course data from booking record
  - Integrate the new utility functions to generate comprehensive payment notification messages
  - Test the updated notification format with various user identification scenarios
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 3. Update alternative payment handler admin notification format
  - Modify `any_message_handler()` in `handlers/message_handlers.py` to use enhanced user identification
  - Update admin notification message format for alternative payment proofs to include course flow information
  - Ensure consistent formatting between photo and alternative payment notifications
  - Test the updated notification format for non-photo payment confirmations
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 4. Implement message preservation for approved payments
  - Modify `handle_admin_approve()` in `handlers/callback_handlers.py` to preserve original message content
  - Replace `query.edit_message_text()` with `query.edit_message_reply_markup()` to remove buttons while keeping content
  - Add approval timestamp and status to the original message using `query.edit_message_text()` with appended content
  - Implement error handling for message update failures with fallback to current behavior
  - _Requirements: 2.1, 2.2, 2.4, 2.5_

- [ ] 5. Add approval timestamp formatting
  - Create utility function to generate UTC timestamp for approval status
  - Format approval status message with clear visual indicators and timestamp
  - Ensure approval status is clearly distinguishable from original payment notification content
  - Test timestamp formatting and UTC conversion accuracy
  - _Requirements: 2.2, 2.4, 2.5_

- [ ] 6. Write comprehensive tests for payment notification enhancements
  - Create unit tests for enhanced message formatting with various user identification scenarios
  - Write integration tests for the complete payment approval workflow with message preservation
  - Test edge cases including users without usernames, special characters in names, and message update failures
  - Verify that rejection workflow remains unchanged and still deletes messages as before
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 7. Verify backward compatibility and admin workflow
  - Test that existing callback data formats and rejection workflow remain unchanged
  - Verify that approved messages maintain chat history accessibility for administrators
  - Ensure that enhanced username information enables direct contact functionality
  - Test the complete payment flow from receipt submission to approval with preserved message content
  - _Requirements: 2.1, 2.3, 2.5_