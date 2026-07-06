"""Tests extraction IP client derrière proxy."""

from unittest.mock import MagicMock

from app.http_utils import obtenir_ip_client


def test_ip_depuis_x_forwarded_for():
    request = MagicMock()
    request.headers = {"X-Forwarded-For": "203.0.113.10, 10.0.0.1"}
    request.client = MagicMock(host="172.18.0.1")
    assert obtenir_ip_client(request) == "203.0.113.10"


def test_ip_depuis_x_real_ip():
    request = MagicMock()
    request.headers = {"X-Real-IP": "198.51.100.5"}
    request.client = MagicMock(host="172.18.0.1")
    assert obtenir_ip_client(request) == "198.51.100.5"


def test_ip_directe_sans_proxy():
    request = MagicMock()
    request.headers = {}
    request.client = MagicMock(host="192.168.1.1")
    assert obtenir_ip_client(request) == "192.168.1.1"
