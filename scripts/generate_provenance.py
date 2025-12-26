#!/usr/bin/env python3
"""
SLSA Level 3 Provenance Generator

Generates SLSA Level 3 compliant provenance metadata for all build artifacts
in accordance with the SLSA specification v1.0

Usage: scripts/generate_provenance.py [--build-id <id>] [--environment <env>]
"""

import argparse
import json
import os
import subprocess
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

class ProvenanceGenerator:
    """Generate SLSA Level 3 provenance for build artifacts"""

    def __init__(self, build_id: str, environment: str, project_root: str):
        self.build_id = build_id
        self.environment = environment
        self.project_root = Path(project_root)
        self.provenance = {}

    def get_git_metadata(self) -> Dict[str, str]:
        """Collect Git repository metadata"""
        metadata = {}

        try:
            # Get current branch
            branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.project_root,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            metadata['branch'] = branch

            # Get commit hash
            commit_hash = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.project_root,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            metadata['commit_hash'] = commit_hash

            # Get remote URL
            remote_url = subprocess.check_output(
                ['git', 'config', '--get', 'remote.origin.url'],
                cwd=self.project_root,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            metadata['remote_url'] = remote_url

            # Get commit message
            commit_message = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=%B'],
                cwd=self.project_root,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            metadata['commit_message'] = commit_message

            # Get author
            author = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=%an <%ae>'],
                cwd=self.project_root,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            metadata['author'] = author

            # Get commit timestamp
            commit_timestamp = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=%ct'],
                cwd=self.project_root,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            metadata['commit_timestamp'] = commit_timestamp

        except subprocess.CalledProcessError:
            metadata['branch'] = 'unknown'
            metadata['commit_hash'] = 'unknown'
            metadata['remote_url'] = 'unknown'

        return metadata

    def get_build_metadata(self) -> Dict[str, Any]:
        """Collect build environment metadata"""
        metadata = {
            "build_id": self.build_id,
            "environment": self.environment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "builder": {
                "id": f"psychsync-builder-{self.environment}",
                "version": "1.0.0",
                "builder_type": "GitHub Actions" if os.getenv('GITHUB_ACTIONS') else "Local"
            },
            "hostname": os.uname().nodename,
            "os": {
                "name": os.uname().sysname,
                "version": os.uname().release,
                "arch": os.uname().machine
            }
        }

        # Add CI-specific metadata
        if os.getenv('GITHUB_ACTIONS'):
            metadata['ci'] = {
                "platform": "GitHub Actions",
                "run_id": os.getenv('GITHUB_RUN_ID'),
                "run_number": os.getenv('GITHUB_RUN_NUMBER'),
                "run_attempt": os.getenv('GITHUB_RUN_ATTEMPT'),
                "repository": os.getenv('GITHUB_REPOSITORY'),
                "ref": os.getenv('GITHUB_REF'),
                "sha": os.getenv('GITHUB_SHA'),
                "actor": os.getenv('GITHUB_ACTOR'),
                "workflow": os.getenv('GITHUB_WORKFLOW'),
                "head_ref": os.getenv('GITHUB_HEAD_REF'),
                "base_ref": os.getenv('GITHUB_BASE_REF')
            }

        return metadata

    def get_materials(self, git_metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """List all materials (inputs) used in the build"""
        materials = []

        # Git repository as material
        materials.append({
            "uri": f"{git_metadata.get('remote_url', 'unknown')}@{git_metadata.get('commit_hash', 'unknown')}",
            "digest": {
                "sha1": git_metadata.get('commit_hash', 'unknown')
            },
            "type": "git"
        })

        # Requirements.txt as material
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            with open(requirements_file, 'rb') as f:
                requirements_hash = hashlib.sha256(f.read()).hexdigest()

            materials.append({
                "uri": "file://requirements.txt",
                "digest": {"sha256": requirements_hash},
                "type": "file"
            })

        # Package files as materials
        for package_file in ['package.json', 'package-lock.json']:
            file_path = self.project_root / "frontend" / package_file
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()

                materials.append({
                    "uri": f"file://frontend/{package_file}",
                    "digest": {"sha256": file_hash},
                    "type": "file"
                })

        return materials

    def get_dependencies(self) -> List[Dict[str, str]]:
        """List all runtime dependencies"""
        dependencies = []

        # Python dependencies
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse package name
                        if '>=' in line or '==' in line:
                            name = line.split('>=')[0].split('==')[0].strip()
                        else:
                            name = line

                        dependencies.append({
                            "name": name,
                            "type": "python",
                            "purl": f"pkg:pypi/{name}"
                        })

        # Node.js dependencies
        package_file = self.project_root / "frontend" / "package.json"
        if package_file.exists():
            with open(package_file, 'r') as f:
                package_data = json.load(f)

            for name, version in package_data.get('dependencies', {}).items():
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "node",
                    "purl": f"pkg:npm/{name}@{version}"
                })

        return dependencies

    def generate_artifact_provenance(
        self,
        artifact_path: str,
        artifact_type: str,
        git_metadata: Dict[str, str],
        build_metadata: Dict[str, Any],
        materials: List[Dict[str, Any]],
        dependencies: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Generate provenance for a single artifact"""

        # Calculate artifact hash
        sha256_hash = hashlib.sha256()
        with open(artifact_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        digest = sha256_hash.hexdigest()

        # Create SLSA provenance
        provenance = {
            "_type": "https://in-toto.io/Statement/v0.1",
            "predicateType": "https://slsa.dev/provenance/v0.2",
            "subject": [
                {
                    "name": os.path.basename(artifact_path),
                    "digest": {
                        "sha256": digest
                    },
                    "size": os.path.getsize(artifact_path),
                    "type": artifact_type
                }
            ],
            "predicate": {
                "builder": {
                    "id": build_metadata["builder"]["id"],
                    "version": build_metadata["builder"]["version"],
                    "builder_type": build_metadata["builder"]["builder_type"]
                },
                "buildType": "https://slsa.dev/secure-builds/v1",
                "invocation": {
                    "configSource": {
                        "uri": f"{git_metadata.get('remote_url', 'unknown')}@{git_metadata.get('commit_hash', 'unknown')}",
                        "digest": {
                            "sha1": git_metadata.get('commit_hash', 'unknown')
                        },
                        "entryPoint": "scripts/sign_build_artifacts.sh"
                    },
                    "parameters": {
                        "environment": self.environment,
                        "build_id": self.build_id,
                        "artifact_type": artifact_type
                    },
                    "environment": {
                        "hostname": build_metadata.get("hostname", "unknown"),
                        "os": build_metadata.get("os", {})
                    }
                },
                "buildConfig": {
                    "artifact_type": artifact_type,
                    "dependencies": dependencies,
                    "materials_count": len(materials)
                },
                "materials": materials,
                "metadata": {
                    "build_timestamp": build_metadata["timestamp"],
                    "git_branch": git_metadata.get("branch", "unknown"),
                    "git_author": git_metadata.get("author", "unknown"),
                    "ci_metadata": build_metadata.get("ci", {})
                }
            }
        }

        return provenance

    def generate_all_provenance(self, artifacts_dir: str, output_dir: str):
        """Generate provenance for all artifacts in the artifacts directory"""

        print(f"Generating SLSA Level 3 provenance...")
        print(f"Build ID: {self.build_id}")
        print(f"Environment: {self.environment}")
        print(f"Artifacts directory: {artifacts_dir}")
        print(f"Output directory: {output_dir}")
        print()

        # Collect metadata
        git_metadata = self.get_git_metadata()
        build_metadata = self.get_build_metadata()
        materials = self.get_materials(git_metadata)
        dependencies = self.get_dependencies()

        print(f"Git metadata:")
        print(f"  Branch: {git_metadata.get('branch', 'unknown')}")
        print(f"  Commit: {git_metadata.get('commit_hash', 'unknown')}")
        print(f"  Author: {git_metadata.get('author', 'unknown')}")
        print()

        print(f"Materials: {len(materials)}")
        print(f"Dependencies: {len(dependencies)}")
        print()

        # Find all artifacts
        artifacts_path = Path(artifacts_dir)
        if not artifacts_path.exists():
            print(f"⚠ Artifacts directory not found: {artifacts_dir}")
            return

        # Generate provenance for each artifact
        provenance_count = 0
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Process manifest file if exists
        manifest_file = artifacts_path / f"manifest-{self.build_id}.json"
        if manifest_file.exists():
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)

            # Generate provenance for Docker images
            for image in manifest.get('docker_images', []):
                image_name = image['name']
                print(f"Generating provenance for: {image_name}")

                # Docker image provenance (reference-based)
                provenance = {
                    "_type": "https://in-toto.io/Statement/v0.1",
                    "predicateType": "https://slsa.dev/provenance/v0.2",
                    "subject": [
                        {
                            "name": image_name,
                            "digest": {
                                "sha256": image.get('image_id', 'unknown')
                            }
                        }
                    ],
                    "predicate": {
                        "builder": build_metadata["builder"],
                        "buildType": "https://slsa.dev/secure-builds/v1",
                        "invocation": {
                            "configSource": {
                                "uri": f"{git_metadata.get('remote_url', 'unknown')}@{git_metadata.get('commit_hash', 'unknown')}",
                                "digest": {"sha1": git_metadata.get('commit_hash', 'unknown')}
                            },
                            "parameters": {
                                "environment": self.environment,
                                "image_name": image_name
                            }
                        },
                        "materials": materials
                    }
                }

                provenance_file = output_path / f"{image_name.replace(':', '-')}.provenance.json"
                with open(provenance_file, 'w') as f:
                    json.dump(provenance, f, indent=2)

                print(f"  ✓ {provenance_file.name}")
                provenance_count += 1

            # Generate provenance for artifacts
            for artifact in manifest.get('artifacts', []):
                artifact_path = artifact['path']
                artifact_type = artifact.get('type', 'unknown')

                if not os.path.exists(artifact_path):
                    print(f"⚠ Artifact not found: {artifact_path}")
                    continue

                print(f"Generating provenance for: {artifact['name']}")

                provenance = self.generate_artifact_provenance(
                    artifact_path,
                    artifact_type,
                    git_metadata,
                    build_metadata,
                    materials,
                    dependencies
                )

                provenance_file = output_path / f"{artifact['name']}.provenance.json"
                with open(provenance_file, 'w') as f:
                    json.dump(provenance, f, indent=2)

                print(f"  ✓ {provenance_file.name}")
                provenance_count += 1

        # Generate consolidated provenance manifest
        manifest = {
            "build_id": self.build_id,
            "environment": self.environment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "generator": {
                "name": "PsychSync SLSA Provenance Generator",
                "version": "1.0.0"
            },
            "git_metadata": git_metadata,
            "build_metadata": build_metadata,
            "provenance_files": provenance_count,
            "artifacts": []
        }

        manifest_file = output_path / f"provenance-manifest-{self.build_id}.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

        print()
        print(f"{'='*80}")
        print(f"Provenance Generation Complete")
        print(f"{'='*80}")
        print(f"Build ID: {self.build_id}")
        print(f"Environment: {self.environment}")
        print(f"Provenance files generated: {provenance_count}")
        print(f"Output directory: {output_dir}")
        print(f"Manifest: {manifest_file}")
        print(f"{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate SLSA Level 3 provenance for build artifacts"
    )
    parser.add_argument(
        '--build-id',
        default=f"build-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        help="Build ID (default: auto-generated)"
    )
    parser.add_argument(
        '--environment',
        default=os.getenv('ENVIRONMENT', 'development'),
        help="Build environment (default: ENVIRONMENT env var or 'development')"
    )
    parser.add_argument(
        '--artifacts-dir',
        default='build/artifacts',
        help="Directory containing build artifacts"
    )
    parser.add_argument(
        '--output-dir',
        default='build/provenance',
        help="Output directory for provenance files"
    )
    parser.add_argument(
        '--project-root',
        default=os.getcwd(),
        help="Project root directory"
    )

    args = parser.parse_args()

    # Create generator
    generator = ProvenanceGenerator(
        build_id=args.build_id,
        environment=args.environment,
        project_root=args.project_root
    )

    # Generate provenance
    generator.generate_all_provenance(
        artifacts_dir=args.artifacts_dir,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
