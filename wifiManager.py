import badger2040
import badger_os
import sys, os
import WIFI_CONFIG


def status_handler(mode, status, ip):
    print(mode, status, ip)
    if status:
        print("Connected!", 10, 10, 300, 0.5)
        print(ip, 10, 30, 300, 0.5)
    else:
        print("Connecting...", 10, 10, 300, 0.5)


def try_connect_wifi(SSID, PSK):
    from network_manager import NetworkManager
    import uasyncio
    import gc

    global isConnecting
    global wifi_loop

    print("try connect wifi")

    uasyncio.get_event_loop().stop()
    if WIFI_CONFIG.COUNTRY == "":
        raise RuntimeError("You must populate WIFI_CONFIG.py for networking.")
    network_manager = NetworkManager(
        WIFI_CONFIG.COUNTRY, client_timeout=5, status_handler=status_handler
    )
    try:
        wifi_loop = uasyncio.get_event_loop().run_until_complete(network_manager.client(SSID, PSK))
        wifi_loop.stop()
    except Exception as e:
        print("WIFI CONNECTION FAILED because: ", e)
        return False
        pass
    isConnecting = False
    gc.collect()


def thread_broadcast():
    global connection_failed
    global last_connection_attempt
    if connection_failed:
        connection_delay = WIFI_CONFIG.WIFI_CONNECTION_DELAY * 5
    else:
        connection_delay = WIFI_CONFIG.WIFI_CONNECTION_DELAY

    if time_elapsed(last_connection_attempt) > connection_delay and not display.isconnected():
        last_connection_attempt = time.time()

        connection_failed = try_connect_wifi(WIFI_CONFIG.SSID_1, WIFI_CONFIG.PSK_1)
        if connection_failed:
            connection_failed = try_connect_wifi(WIFI_CONFIG.SSID_2, WIFI_CONFIG.PSK_2)
    # if display.isconnected():
    #     handle_broadcast()
