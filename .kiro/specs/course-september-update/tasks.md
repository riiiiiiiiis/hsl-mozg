# Implementation Plan

- [x] 1. Update course constants with September dates and 4th stream branding
  - Modify COURSES array in constants.py to change start dates from "12 августа" to "1 сентября"
  - Update course descriptions to include "ЧЕТВЕРТЫЙ ПОТОК ВАЙБКОДИНГА" branding
  - Update both CORE and EXTRA course variants with consistent information and new schedule
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 6.1, 6.2, 6.3, 6.4_

- [x] 2. Update free lesson constants for "Вайбкодинг с Cursor"
  - Modify FREE_LESSON dictionary in constants.py to reflect new lesson format
  - Change title from "Бесплатный первый урок" to "Вайбкодинг с Cursor"
  - Update button_text to "🆓 Вайбкодинг с Cursor"
  - Create new description content focusing on Cursor tool usage
  - Update date_text to align with new schedule
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 4.2, 4.3_

- [x] 3. Create database migration script for lesson type field
  - Write migration script to add lesson_type column to free_lesson_registrations table
  - Set default value to 'cursor_lesson' for new registrations
  - Include rollback functionality in case migration needs to be reverted
  - Add proper error handling and logging for migration process
  - _Requirements: 3.1, 4.1, 5.1, 5.2_

- [x] 4. Implement data migration for existing registrations
  - Create script to update existing free_lesson_registrations with lesson_type = 'vibecoding_lesson'
  - Ensure migration handles edge cases and maintains data integrity
  - Add verification step to confirm all existing records are properly updated
  - Log migration results for audit purposes
  - _Requirements: 3.4, 5.1, 5.2, 5.3_

- [x] 5. Update free_lessons.py database functions for lesson types
  - Modify create_free_lesson_registration() to accept lesson_type parameter with default 'cursor_lesson'
  - Update function to save lesson_type in database during registration
  - Ensure backward compatibility with existing function calls
  - Add proper validation for lesson_type values
  - _Requirements: 3.1, 3.2, 4.4_

- [x] 6. Add new database functions for lesson type filtering and statistics
  - Implement get_registrations_by_type(lesson_type) function to filter registrations
  - Create get_registration_stats() function to return counts grouped by lesson type
  - Add get_all_registrations_with_type() function for admin interface
  - Include proper error handling and logging in all new functions
  - _Requirements: 3.2, 3.3, 5.4_

- [x] 7. Update database setup to include new columns for lesson types and course streams
  - Modify setup_database() function in db/base.py to include lesson_type column in free_lesson_registrations
  - Add course_stream column to bookings table with default value '4th_stream'
  - Ensure new installations automatically have both new fields
  - Add proper column constraints and default values for both tables
  - Test that fresh database setup works correctly with updated schema
  - _Requirements: 4.1, 5.1_

- [x] 8. Update booking functions to include course stream tracking
  - Modify booking creation functions in db/bookings.py to save course_stream field
  - Set default course_stream to '4th_stream' for all new bookings
  - Add functions to filter bookings by course stream for admin statistics
  - Ensure backward compatibility with existing booking functionality
  - _Requirements: 3.1, 3.2, 5.4_

- [x] 9. Create comprehensive tests for updated constants and functionality
  - Write unit tests for updated COURSES and FREE_LESSON constants validation
  - Create tests for new database functions with lesson type and course stream support
  - Add integration tests for complete registration flow with new lesson types
  - Test migration scripts with sample data to ensure proper functionality
  - Test booking functions with course stream tracking
  - _Requirements: 4.3, 5.4_

- [x] 10. Update bot handlers to work with new lesson type system
  - Ensure callback handlers properly use updated FREE_LESSON constants
  - Verify that course selection displays updated information with "4-й поток" branding
  - Test that free lesson registration flow works with new lesson type
  - Confirm that all user-facing messages reflect the new "Вайбкодинг с Cursor" branding
  - _Requirements: 2.1, 2.2, 2.3, 4.3, 6.1, 6.2, 6.4_

- [x] 11. Run end-to-end testing and validation
  - Test complete user journey from course selection to registration with updated information
  - Verify that existing users see updated course dates and "4-й поток" descriptions
  - Test new free lesson registration creates records with correct lesson_type
  - Test new course bookings create records with correct course_stream
  - Validate that admin statistics show proper breakdown by lesson types and course streams
  - Confirm that all date references are consistently updated throughout the system
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 5.4, 6.1, 6.2, 6.3, 6.4_