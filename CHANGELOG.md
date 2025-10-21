# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial WebSocket notification server implementation
- Real-time WebSocket communication with automatic client management
- Periodic notification service with configurable intervals
- On-demand broadcasting via HTTP API
- Graceful shutdown with connection monitoring and timeout management
- Multi-worker support for horizontal scaling
- Comprehensive logging with structured JSON format
- Health check and metrics endpoints
- Prometheus metrics integration
- Docker support with development and production configurations
- Complete test suite with unit, integration, and performance tests
- Production-ready configuration management
- Error handling and recovery mechanisms

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- Input validation with Pydantic models
- Sanitized error messages in production
- Non-root user in Docker containers

## [0.1.0] - 2024-10-21

### Added
- Initial project setup
- Core WebSocket server functionality
- Basic notification system
- Docker containerization
- Comprehensive documentation