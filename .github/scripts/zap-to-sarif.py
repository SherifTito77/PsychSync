#!/usr/bin/env python3
"""
ZAP XML to SARIF Converter

Converts OWASP ZAP XML report to SARIF format for GitHub Security.
"""

import argparse
import json
from datetime import datetime
from xml.etree import ElementTree as ET


def zap_to_sarif(input_file: str, output_file: str, target_url: str):
    """Convert ZAP XML report to SARIF format"""

    # Parse ZAP XML
    tree = ET.parse(input_file)
    root = tree.getroot()

    # SARIF template
    sarif = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "OWASP ZAP",
                        "version": "2.14.0",
                        "informationUri": "https://www.zaproxy.org/",
                        "rules": []
                    }
                },
                "automationDetails": {
                    "id": "zap-dast-scan",
                    "guid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                },
                "results": [],
                "invocations": [
                    {
                        "startTimeUtc": datetime.utcnow().isoformat() + "Z",
                        "endTimeUtc": datetime.utcnow().isoformat() + "Z"
                    }
                ]
            }
        ]
    }

    # Extract alerts and convert to SARIF results
    rules_seen = set()

    for alert in root.findall('.//alert'):
        # Extract alert details
        plugin_id = alert.find('pluginid').text
        alert_level = alert.find('riskcode').text
        name = alert.find('name').text
        description = alert.find('desc').text

        # Get alert location
        location_elem = alert.find('location')
        if location_elem is not None:
            uri = location_elem.find('uri').text if location_elem.find('uri') is not None else target_url
        else:
            uri = target_url

        # Create rule if not seen
        if plugin_id not in rules_seen:
            rule = {
                "id": f"ZAP-{plugin_id}",
                "name": name,
                "shortDescription": {
                    "text": description
                },
                "fullDescription": {
                    "text": alert.find('solution').text if alert.find('solution') is not None else description
                },
                "help": {
                    "text": alert.find('desc').text if alert.find('desc') is not None else description
                },
                "properties": {
                    "riskCode": alert_level,
                    "confidence": alert.find('confidence').text if alert.find('confidence') is not None else "0"
                }
            }

            # Add references if available
            refs_elem = alert.find('refs')
            if refs_elem is not None and refs_elem.text:
                rule["helpUri"] = refs_elem.text

            sarif["runs"][0]["tool"]["driver"]["rules"].append(rule)
            rules_seen.add(plugin_id)

        # Create result
        # Map riskcode to severity level
        risk_level = int(alert_level)
        if risk_level == 3:
            level = "error"
        elif risk_level == 2:
            level = "warning"
        elif risk_level == 1:
            level = "note"
        else:
            level = "none"

        result = {
            "ruleId": f"ZAP-{plugin_id}",
            "level": level,
            "message": {
                "text": description
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": uri
                        },
                        "region": {
                            "startLine": 1,
                            "startColumn": 1
                        }
                    }
                }
            ]
        }

        # Add CWE if available
        cwe_elem = alert.find('cweid')
        if cwe_elem is not None and cwe_elem.text:
            result["ruleId"] = f"CWE-{cwe_elem.text}"

        sarif["runs"][0]["results"].append(result)

    # Write SARIF output
    with open(output_file, 'w') as f:
        json.dump(sarif, f, indent=2)

    print(f"✅ Converted {len(sarif['runs'][0]['results'])} ZAP findings to SARIF format")
    print(f"📁 Output: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Convert ZAP XML to SARIF')
    parser.add_argument('--input', required=True, help='ZAP XML input file')
    parser.add_argument('--output', required=True, help='SARIF output file')
    parser.add_argument('--target-url', required=True, help='Target URL that was scanned')

    args = parser.parse_args()

    zap_to_sarif(args.input, args.output, args.target_url)


if __name__ == '__main__':
    main()
