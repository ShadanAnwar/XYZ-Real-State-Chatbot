import unittest
import os
import time
import random
from dotenv import load_dotenv
from crm.hubspot_client import create_or_update_contact

load_dotenv()

class TestCRMIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate unique test data
        cls.timestamp = str(int(time.time()))
        cls.test_email = f"testuser_{cls.timestamp}@example.com"
        cls.test_name = f"Test User {cls.timestamp}"
        cls.test_location = "Test City"
        cls.test_budget = random.randint(100000, 1000000)

    def test_1_create_new_contact(self):
        """Test creating a new contact in CRM"""
        status, response = create_or_update_contact(
            email=self.test_email,
            name=self.test_name,
            location=self.test_location,
            budget=self.test_budget,
            lead_score=75,
            lead_status="Hot",
            chat_history="Test conversation"
        )

        # Check response
        self.assertIn(status, [200, 201], 
            f"Expected status 200/201, got {status}. Response: {response}")
        
        # Verify created data
        if status == 201:  # New creation
            self.assertEqual(response['properties']['email'], self.test_email)
            self.assertEqual(response['properties']['firstname'], self.test_name)
            self.assertEqual(response['properties']['location'], self.test_location)
        print("Create Contact Test Passed")

    def test_2_update_existing_contact(self):
        """Test updating an existing contact"""
        updated_budget = self.test_budget + 50000
        updated_status = "Warm"

        status, response = create_or_update_contact(
            email=self.test_email,
            name=self.test_name,
            location=self.test_location,
            budget=updated_budget,
            lead_score=60,
            lead_status=updated_status,
            chat_history="Updated conversation"
        )

        self.assertEqual(status, 200, 
            f"Expected status 200, got {status}. Response: {response}")
        self.assertEqual(response['properties']['budget'], str(updated_budget))
        self.assertEqual(response['properties']['lead_status'], updated_status)
        print("Update Contact Test Passed")

    def test_3_error_handling(self):
        """Test error handling for invalid requests"""
        # Test invalid email format
        status, response = create_or_update_contact(
            email="invalid-email",
            name="Test",
            location="Test",
            budget=0,
            lead_score=0,
            lead_status="",
            chat_history=""
        )

        self.assertNotEqual(status, 200, 
            "Should get error for invalid email format")
        print("Error Handling Test Passed")

if __name__ == '__main__':
    unittest.main(verbosity=2)