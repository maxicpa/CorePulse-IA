from corepulse_ai.routing import route_query


def test_route_cpu():
    assert route_query("Temperatura de CPU muy alta") == "cpu"


def test_route_gpu():
    assert route_query("¿Cómo está mi GPU?") == "gpu"


def test_route_memory():
    assert route_query("Tengo mucho uso de RAM") == "memory"


def test_route_storage():
    assert route_query("Revisa mi SSD") == "storage"


def test_route_network():
    assert route_query("Tengo mucha latencia de red") == "network"


def test_route_general():
    # pero verifica tanto system como el fallback general.
    assert route_query("Revisa el estado del sistema Windows") == "system"
    assert route_query("Analiza este equipo") == "general"
