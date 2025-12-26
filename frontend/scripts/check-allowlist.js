#!/usr/bin/env node
/**
 * Check that all npm dependencies are in allow-list
 * Fails CI if any dependency is not allowed
 *
 * Usage: node scripts/check-allowlist.js
 * Exit code: 0 (all allowed), 1 (violations found)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');


/**
 * Get list of installed packages from package-lock.json
 */
function getInstalledPackages() {
    const lockfilePath = path.join(process.cwd(), 'package-lock.json');

    if (!fs.existsSync(lockfilePath)) {
        console.error('❌ package-lock.json not found');
        console.error('   Run: npm install');
        process.exit(1);
    }

    const lockfile = JSON.parse(fs.readFileSync(lockfilePath, 'utf8'));
    const packages = {};

    // Get top-level dependencies
    if (lockfile.packages) {
        for (const [name, info] of Object.entries(lockfile.packages)) {
            // Skip root package
            if (name === '') continue;

            // Only include direct dependencies
            if (info.version && !name.includes('node_modules')) {
                // Get package name without scoped prefix
                const pkgName = name.replace('node_modules/', '');
                packages[pkgName] = info.version;
            }
        }
    }

    return packages;
}


/**
 * Parse allow-list from JSON file
 */
function parseAllowList() {
    const allowListPath = path.join(process.cwd(), 'allowed-dependencies.json');

    if (!fs.existsSync(allowListPath)) {
        console.error(`❌ Allow-list file not found: ${allowListPath}`);
        process.exit(1);
    }

    const allowList = JSON.parse(fs.readFileSync(allowListPath, 'utf8'));

    const allowed = {};

    if (allowList.allowedDependencies) {
        for (const [name, info] of Object.entries(allowList.allowedDependencies)) {
            allowed[name] = {
                versionRange: info.versionRange,
                maxVersion: info.maxVersion,
                signatureRequired: info.signatureRequired || false
            };
        }
    }

    return allowed;
}


/**
 * Check if version is within allowed range
 */
function checkVersionCompliance(package, installedVersion, allowedInfo) {
    const versionRange = allowedInfo.versionRange;
    const maxVersion = allowedInfo.maxVersion;

    // Simple version check (use semver in production)
    // For now, just warn if version exceeds maxVersion
    if (maxVersion && installedVersion > maxVersion) {
        return false;
    }

    return true;
}


/**
 * Main check function
 */
function checkAllowList() {
    console.log('🔍 Checking npm dependencies against allow-list...\n');

    // Get installed packages
    const installed = getInstalledPackages();
    console.log(`📦 Found ${Object.keys(installed).length} installed packages`);

    // Parse allow-list
    const allowList = parseAllowList();
    console.log(`✅ Allow-list has ${Object.keys(allowList).length} allowed packages\n`);

    const violations = [];

    // Check each package
    for (const [name, version] of Object.entries(installed)) {
        if (!allowList[name]) {
            violations.push({
                package: name,
                version: version,
                reason: 'Not in allow-list'
            });
        } else {
            // Check version compliance
            const allowedInfo = allowList[name];
            if (!checkVersionCompliance(name, version, allowedInfo)) {
                violations.push({
                    package: name,
                    version: version,
                    reason: `Version ${version} exceeds max ${allowedInfo.maxVersion}`
                });
            }
        }
    }

    // Report results
    if (violations.length > 0) {
        console.log('❌ DEPENDENCY ALLOW-LIST VIOLATIONS DETECTED');
        console.log(`   ${violations.length} violations found\n`);

        for (const v of violations) {
            console.log(`  • ${v.package} (${v.version})`);
            console.log(`    Reason: ${v.reason}`);
            console.log(`    Action: Submit dependency request\n`);
        }

        console.log('To request an exception:');
        console.log('  1. Create issue:');
        console.log('     gh issue create --title "Dependency Request: PACKAGE" \\');
        console.log('       --label "dependency-request"');
        console.log('  2. Security team reviews within 24-48 hours');
        console.log('  3. Once approved, add to allowed-dependencies.json');
        console.log('\nSee DEPENDENCY_ALLOWLIST_POLICY.md for request template\n');

        process.exit(1);
    } else {
        console.log(`✅ All ${Object.keys(installed).length} dependencies are in allow-list`);
        console.log('   Compliance: 100%\n');
        process.exit(0);
    }
}


// Run the check
checkAllowList();
