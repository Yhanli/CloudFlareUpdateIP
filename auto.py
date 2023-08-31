"""Cloudflare API code - example"""

import os
import sys
import requests
import json
from datetime import datetime

sys.path.insert(0, os.path.abspath(".."))
import CloudFlare


def my_ip_address():
    """Cloudflare API code - example"""

    # This list is adjustable - plus some v6 enabled services are needed
    # url = 'http://myip.dnsomatic.com'
    # url = 'http://www.trackip.net/ip'
    # url = 'http://myexternalip.com/raw'
    url = "https://api.ipify.org"
    try:
        ip_address = requests.get(url).text
    except:
        exit("%s: failed" % (url))
    if ip_address == "":
        exit("%s: failed" % (url))

    if ":" in ip_address:
        ip_address_type = "AAAA"
    else:
        ip_address_type = "A"

    new_ip = f"{ip_address},{ip_address_type}"
    old_ip = ""
    try:
        with open(os.path.join("ip_record"), "r") as fp:
            old_ip = fp.read()
    except:
        print("No old IP have been recorded")

    with open(os.path.join("ip_record"), "w+") as fp:
        fp.write(new_ip)

    if new_ip == old_ip:
        # print(f"IP not changed, {ip_address},{ip_address_type}")
        # print(f"end:{datetime.now()}\n")
        exit()

    return ip_address, ip_address_type


def do_dns_update(cf, zone_name, zone_id, dns_name, ip_address, ip_address_type):
    """Cloudflare API code - example"""
    print(f"start:{datetime.now()}")
    try:
        # params = {"name": dns_name, "match": "all", "type": ip_address_type}
        # dns_records = cf.zones.dns_records.get(zone_id, params=params)
        dns_records = cf.zones.dns_records.get(
            zone_id
        )  # update all name to the same ip, currenly only 1 ip for all name
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit("/zones/dns_records %s - %d %s - api call failed" % (dns_name, e, e))

    # update the record - unless it's already correct
    for dns_record in dns_records:
        old_ip_address = dns_record["content"]
        old_ip_address_type = dns_record["type"]
        og_dns_name = dns_record["name"]
        # china home is handled else where
        if "china-home" in og_dns_name:
            continue

        if ip_address_type not in ["A", "AAAA"]:
            # we only deal with A / AAAA records
            continue

        if ip_address_type != old_ip_address_type:
            # only update the correct address type (A or AAAA)
            # we don't see this becuase of the search params above
            print("IGNORED: %s %s ; wrong address family" % (dns_name, old_ip_address))
            continue

        if ip_address == old_ip_address:
            print("UNCHANGED: %s %s" % (og_dns_name, ip_address))
            continue

        proxied_state = dns_record["proxied"]

        # Yes, we need to update this record - we know it's the same address type

        dns_record_id = dns_record["id"]
        dns_record = {
            "name": og_dns_name,
            "type": ip_address_type,
            "content": ip_address,
            "proxied": proxied_state,
        }
        print(dns_record_id, dns_record)
        try:
            dns_record = cf.zones.dns_records.put(
                zone_id, dns_record_id, data=dns_record
            )
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            exit(
                "/zones.dns_records.put %s - %d %s - api call failed" % (dns_name, e, e)
            )
        print("UPDATED: %s %s -> %s" % (dns_name, old_ip_address, ip_address))

        # if not updated:
        #     # no exsiting dns record to update - so create dns record
        #     dns_record = {
        #         "name": dns_name,
        #         "type": ip_address_type,
        #         "content": ip_address,
        #     }
        #     try:
        #         # dns_record = cf.zones.dns_records.post(zone_id, data=dns_record)
        #         pass
        #     except CloudFlare.exceptions.CloudFlareAPIError as e:
        #         exit(
        #             "/zones.dns_records.post %s - %d %s - api call failed"
        #             % (dns_name, e, e)
        #         )
        #     print("CREATED: %s %s" % (dns_name, ip_address))
    print(f"end:{datetime.now()}\n")


def main():
    """Cloudflare API code - example"""

    try:
        _json = json.load(open(os.path.join("auth.json")))
        token = _json["token"]
        dns_name = _json["site"]
    except IndexError:
        exit("usage: change the auth.json token to your api token key")

    host_name, zone_name = ".".join(dns_name.split(".")[:2]), ".".join(
        dns_name.split(".")[-2:]
    )

    ip_address, ip_address_type = my_ip_address()

    print("MY IP: %s %s" % (dns_name, ip_address))

    cf = CloudFlare.CloudFlare(token=token)

    # grab the zone identifier
    try:
        params = {"name": zone_name}
        zones = cf.zones.get(params=params)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit("/zones %d %s - api call failed" % (e, e))
    except Exception as e:
        exit("/zones.get - %s - api call failed" % (e))

    if len(zones) == 0:
        exit("/zones.get - %s - zone not found" % (zone_name))

    if len(zones) != 1:
        exit("/zones.get - %s - api call returned %d items" % (zone_name, len(zones)))

    zone = zones[0]

    zone_name = zone["name"]
    zone_id = zone["id"]

    print(cf, zone_name, zone_id, dns_name, ip_address, ip_address_type)
    do_dns_update(cf, zone_name, zone_id, dns_name, ip_address, ip_address_type)


if __name__ == "__main__":
    # print(f"start:{datetime.now()}")
    main()
    # print(f"end:{datetime.now()}\n")
