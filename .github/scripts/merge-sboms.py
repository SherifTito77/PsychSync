#!/usr/bin/env python3
"""
SBOM Merge Script

Merges multiple SBOMs (Python, Node.js, etc.) into a single SBOM
for comprehensive vulnerability scanning.
"""

import argparse
import json
from datetime import datetime, timezone
import uuid


def load_sbom(filepath):
    """Load SBOM from JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Warning: Could not load {filepath}: {e}")
        return None


def merge_sboms(python_sbom, frontend_sbom, output_file):
    """Merge Python and frontend SBOMs into single SBOM"""

    # Load SBOMs
    py_components = load_sbom(python_sbom)
    fe_components = load_sbom(frontend_sbom)

    # Create merged SBOM
    merged_sbom = {
        "$schema": "http://cyclonedx.org/schema/bom-1.5.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tools": [
                {
                    "vendor": "PsychSync",
                    "name": "SBOM Merge Tool",
                    "version": "1.0.0"
                },
                {
                    "vendor": "CycloneDX",
                    "name": "cyclonedx-python",
                    "version": "1.0.0"
                }
            ],
            "component": {
                "name": "psychsync",
                "type": "application",
                "purl": "pkg:generic/psychsync",
                "description": "PsychSync Psychology Assessment Platform"
            }
        },
        "components": []
    }

    # Collect all components
    components_set = {}  # Use dict to deduplicate by BOM ref

    # Process Python SBOM
    if py_components and 'components' in py_components:
        print(f"📦 Processing {len(py_components['components'])} Python components...")
        for component in py_components['components']:
            bom_ref = component.get('purl', component.get('bom-ref', ''))
            if bom_ref:
                components_set[bom_ref] = component
                # Add source metadata
                if 'properties' not in component:
                    component['properties'] = []
                component['properties'].append({
                    "name": "psychsync:source",
                    "value": "python-backend"
                })

    # Process Frontend SBOM
    if fe_components and 'components' in fe_components:
        print(f"📦 Processing {len(fe_components['components'])} frontend components...")
        for component in fe_components['components']:
            bom_ref = component.get('purl', component.get('bom-ref', ''))
            if bom_ref:
                if bom_ref in components_set:
                    # Component exists, add source
                    if 'properties' not in components_set[bom_ref]:
                        components_set[bom_ref]['properties'] = []
                    components_set[bom_ref]['properties'].append({
                        "name": "psychsync:source",
                        "value": "nodejs-frontend"
                    })
                else:
                    # New component
                    if 'properties' not in component:
                        component['properties'] = []
                    component['properties'].append({
                        "name": "psychsync:source",
                        "value": "nodejs-frontend"
                    })
                    components_set[bom_ref] = component

    # Add to merged SBOM
    merged_sbom['components'] = list(components_set.values())

    print(f"✅ Merged {len(merged_sbom['components'])} unique components")

    # Write merged SBOM
    with open(output_file, 'w') as f:
        json.dump(merged_sbom, f, indent=2)

    print(f"📁 Merged SBOM saved to: {output_file}")

    # Print summary
    python_count = sum(1 for c in merged_sbom['components']
                      if any(p.get('value') == 'python-backend' for p in c.get('properties', [])))
    frontend_count = sum(1 for c in merged_sbom['components']
                        if any(p.get('value') == 'nodejs-frontend' for p in c.get('properties', [])))

    print("\n📊 Summary:")
    print(f"  Python components: {python_count}")
    print(f"  Frontend components: {frontend_count}")
    print(f"  Total unique components: {len(merged_sbom['components'])}")


def main():
    parser = argparse.ArgumentParser(description='Merge multiple SBOMs into one')
    parser.add_argument('--python', required=True, help='Python SBOM file')
    parser.add_argument('--frontend', required=True, help='Frontend SBOM file')
    parser.add_argument('--output', required=True, help='Output merged SBOM file')

    args = parser.parse_args()

    merge_sboms(args.python, args.frontend, args.output)


if __name__ == '__main__':
    main()
