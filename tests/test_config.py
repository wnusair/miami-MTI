"""
Test cases for configuration settings.
"""

import pytest
import os
from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig


class TestConfiguration:
    """Test configuration classes."""
    
    def test_base_config(self):
        """Test base configuration."""
        assert Config.SQLALCHEMY_TRACK_MODIFICATIONS is False
    
    def test_development_config(self):
        """Test development configuration."""
        assert DevelopmentConfig.DEBUG is True
    
    def test_production_config(self):
        """Test production configuration."""
        assert ProductionConfig.DEBUG is False
    
    def test_testing_config(self):
        """Test testing configuration."""
        assert TestingConfig.TESTING is True
        assert TestingConfig.SQLALCHEMY_DATABASE_URI == 'sqlite:///:memory:'
        assert TestingConfig.WTF_CSRF_ENABLED is False
    
    def test_parse_cors_origins_wildcard(self):
        """Test parsing CORS origins with wildcard."""
        result = Config.parse_cors_origins('*')
        assert result == '*'
    
    def test_parse_cors_origins_single(self):
        """Test parsing single CORS origin."""
        result = Config.parse_cors_origins('https://example.com')
        assert result == ['https://example.com']
    
    def test_parse_cors_origins_multiple(self):
        """Test parsing multiple CORS origins."""
        result = Config.parse_cors_origins('https://example.com, https://test.com')
        assert len(result) == 2
        assert 'https://example.com' in result
        assert 'https://test.com' in result
    
    def test_parse_cors_origins_empty(self):
        """Test parsing empty CORS origins."""
        result = Config.parse_cors_origins('')
        assert result == '*'
    
    def test_secret_key_validation(self):
        """Test SECRET_KEY validation."""
        from app import create_app
        from flask import Flask
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = None
        
        with pytest.raises(ValueError, match='SECRET_KEY is not set'):
            Config.init_app(app)
    
    def test_secret_key_length_validation(self):
        """Test SECRET_KEY length validation."""
        from flask import Flask
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'short'
        
        with pytest.raises(ValueError, match='too short'):
            Config.init_app(app)
    
    def test_secret_key_valid(self):
        """Test valid SECRET_KEY passes."""
        from flask import Flask
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'a' * 32
        
        Config.init_app(app)
