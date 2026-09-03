#!/usr/bin/env node
/**
 * Comprehensive View Details Functionality Test
 * Tests the wellness assessment View Details buttons and data display
 */

const puppeteer = require('puppeteer');

class ViewDetailsTester {
    constructor() {
        this.testResults = [];
        this.browser = null;
        this.page = null;
    }

    async setup() {
        console.log('🚀 Setting up View Details test environment...');

        this.browser = await puppeteer.launch({
            headless: false, // Show browser for debugging
            defaultViewport: { width: 1200, height: 800 },
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        this.page = await this.browser.newPage();

        // Enable console logging from the page
        this.page.on('console', msg => {
            if (msg.text().includes('View Details') || msg.text().includes('🎯')) {
                console.log('📝 Browser Console:', msg.text());
            }
        });

        // Enable request monitoring
        this.page.on('request', request => {
            if (request.url().includes('/api/')) {
                console.log('🌐 API Request:', request.method(), request.url());
            }
        });
    }

    async navigateToWellnessPage() {
        console.log('🧭 Navigating to Wellness Plan Generator...');

        try {
            // Navigate to the main app first
            await this.page.goto('http://localhost:5174/', { waitUntil: 'networkidle2' });
            await this.page.waitForTimeout(2000);

            // Look for wellness navigation
            const wellnessLink = await this.page.$('a[href*="wellness"], button:contains("Wellness"), .wellness-nav');
            if (wellnessLink) {
                await wellnessLink.click();
                console.log('✅ Found and clicked wellness navigation');
            } else {
                // Try to navigate directly to mental health wellness page
                await this.page.goto('http://localhost:5174/mental-health-wellness', { waitUntil: 'networkidle2' });
            }

            await this.page.waitForTimeout(3000);

            // Check if we're on the right page
            const pageTitle = await this.page.title();
            const pageContent = await this.page.content();

            if (pageContent.includes('Wellness Plan') || pageContent.includes('Mental Health')) {
                console.log('✅ Successfully navigated to wellness page');
                return true;
            } else {
                console.log('❌ Could not find wellness page content');
                return false;
            }

        } catch (error) {
            console.log('❌ Error navigating to wellness page:', error.message);
            return false;
        }
    }

    async testWellnessPlanGeneration() {
        console.log('📋 Testing Wellness Plan Generation...');

        try {
            // Look for wellness plan form
            const generateButton = await this.page.$('button:contains("Generate Plan"), button:contains("Create Plan"), .generate-plan-btn');

            if (generateButton) {
                await generateButton.click();
                console.log('✅ Clicked Generate Plan button');
                await this.page.waitForTimeout(2000);

                // Fill out a basic wellness form if it appears
                const domainSelectors = await this.page.$$('input[type="radio"], .domain-option, .wellness-domain');
                if (domainSelectors.length > 0) {
                    await domainSelectors[0].click();
                    console.log('✅ Selected wellness domain');

                    // Look for submit button
                    const submitButton = await this.page.$('button:contains("Submit"), button:contains("Continue"), .submit-btn');
                    if (submitButton) {
                        await submitButton.click();
                        console.log('✅ Submitted wellness form');
                        await this.page.waitForTimeout(3000);
                    }
                }
            } else {
                console.log('⚠️  No generate plan button found, looking for existing plan...');
            }

            // Check if wellness plan is displayed
            const planContent = await this.page.content();
            const hasWellnessGoals = planContent.includes('wellness goal') ||
                                   planContent.includes('action step') ||
                                   planContent.includes('milestone');

            if (hasWellnessGoals) {
                console.log('✅ Wellness plan content found');
                return true;
            } else {
                console.log('❌ No wellness plan content found');
                return false;
            }

        } catch (error) {
            console.log('❌ Error in wellness plan generation test:', error.message);
            return false;
        }
    }

    async testViewDetailsButtons() {
        console.log('🔍 Testing View Details buttons...');

        const viewDetailsResults = {
            buttonsFound: 0,
            buttonsWorking: 0,
            detailsDisplayed: 0,
            errors: []
        };

        try {
            // Find all View Details buttons
            const viewDetailsButtons = await this.page.$$('button:contains("View Details"), .view-details-btn');
            viewDetailsResults.buttonsFound = viewDetailsButtons.length;

            console.log(`📊 Found ${viewDetailsButtons.length} View Details buttons`);

            if (viewDetailsButtons.length === 0) {
                // Try alternative selectors
                const altButtons = await this.page.$$('[title*="Details"], button[onclick*="Details"]');
                viewDetailsResults.buttonsFound = altButtons.length;
                console.log(`📊 Found ${altButtons.length} alternative View Details buttons`);
            }

            // Test each View Details button
            for (let i = 0; i < Math.min(viewDetailsResults.buttonsFound, 3); i++) {
                try {
                    const button = viewDetailsButtons[i] || (await this.page.$$('[title*="Details"]'))[i];

                    if (button) {
                        // Take screenshot before clicking
                        await this.page.screenshot({
                            path: `test_screenshots/before_view_details_${i}.png`,
                            fullPage: false
                        });

                        console.log(`🎯 Testing View Details button ${i + 1}`);

                        // Click the button
                        await button.click();
                        viewDetailsResults.buttonsWorking++;

                        // Wait for potential modal or detailed view
                        await this.page.waitForTimeout(2000);

                        // Check if detailed view appeared
                        const pageContent = await this.page.content();
                        const hasDetails = pageContent.includes('progress') ||
                                        pageContent.includes('action steps') ||
                                        pageContent.includes('milestone') ||
                                        pageContent.includes('Back to Plan') ||
                                        pageContent.includes('detailed view');

                        if (hasDetails) {
                            viewDetailsResults.detailsDisplayed++;
                            console.log(`✅ View Details button ${i + 1} working - details displayed`);

                            // Take screenshot of details
                            await this.page.screenshot({
                                path: `test_screenshots/view_details_${i}_working.png`,
                                fullPage: false
                            });

                            // Try to go back
                            const backButton = await this.page.$('button:contains("Back"), .back-btn, ←');
                            if (backButton) {
                                await backButton.click();
                                await this.page.waitForTimeout(1000);
                            }
                        } else {
                            console.log(`❌ View Details button ${i + 1} clicked but no details displayed`);
                            viewDetailsResults.errors.push(`Button ${i + 1}: No details displayed`);
                        }
                    }
                } catch (buttonError) {
                    console.log(`❌ Error testing View Details button ${i + 1}:`, buttonError.message);
                    viewDetailsResults.errors.push(`Button ${i + 1}: ${buttonError.message}`);
                }
            }

        } catch (error) {
            console.log('❌ Error in View Details test:', error.message);
            viewDetailsResults.errors.push(`General error: ${error.message}`);
        }

        return viewDetailsResults;
    }

    async testWellnessDataIntegration() {
        console.log('📊 Testing wellness data integration...');

        const dataResults = {
            hasGoals: false,
            hasActionSteps: false,
            hasProgress: false,
            hasAIInsights: false,
            apiCalls: 0,
            errors: []
        };

        try {
            // Monitor API calls during View Details interaction
            const apiRequests = [];
            this.page.on('request', request => {
                if (request.url().includes('/api/wellness') ||
                    request.url().includes('/api/assessment') ||
                    request.url().includes('/api/plan')) {
                    apiRequests.push(request.url());
                    dataResults.apiCalls++;
                }
            });

            // Look for wellness data in the page
            const pageContent = await this.page.content();

            dataResults.hasGoals = pageContent.includes('goal') || pageContent.includes('objective');
            dataResults.hasActionSteps = pageContent.includes('action step') || pageContent.includes('step');
            dataResults.hasProgress = pageContent.includes('progress') || pageContent.includes('% complete');
            dataResults.hasAIInsights = pageContent.includes('AI') || pageContent.includes('insight') || pageContent.includes('recommendation');

            console.log('📈 Wellness Data Integration Results:');
            console.log(`   Goals: ${dataResults.hasGoals ? '✅' : '❌'}`);
            console.log(`   Action Steps: ${dataResults.hasActionSteps ? '✅' : '❌'}`);
            console.log(`   Progress: ${dataResults.hasProgress ? '✅' : '❌'}`);
            console.log(`   AI Insights: ${dataResults.hasAIInsights ? '✅' : '❌'}`);
            console.log(`   API Calls: ${dataResults.apiCalls}`);

            if (dataResults.apiCalls === 0 && (dataResults.hasGoals || dataResults.hasActionSteps)) {
                dataResults.errors.push('Data present but no API calls detected - possible static/mock data');
            }

        } catch (error) {
            console.log('❌ Error in wellness data integration test:', error.message);
            dataResults.errors.push(error.message);
        }

        return dataResults;
    }

    async generateTestReport(results) {
        console.log('\n📋 VIEW DETAILS FUNCTIONALITY TEST REPORT');
        console.log('=' * 50);

        const viewDetailsResults = results.viewDetailsTest;
        const dataResults = results.dataIntegrationTest;

        console.log('\n🎯 View Details Button Test:');
        console.log(`   Buttons Found: ${viewDetailsResults.buttonsFound}`);
        console.log(`   Buttons Working: ${viewDetailsResults.buttonsWorking}`);
        console.log(`   Details Displayed: ${viewDetailsResults.detailsDisplayed}`);

        if (viewDetailsResults.errors.length > 0) {
            console.log('\n❌ View Details Errors:');
            viewDetailsResults.errors.forEach(error => console.log(`   • ${error}`));
        }

        console.log('\n📊 Wellness Data Integration:');
        console.log(`   Goals Present: ${dataResults.hasGoals ? '✅' : '❌'}`);
        console.log(`   Action Steps Present: ${dataResults.hasActionSteps ? '✅' : '❌'}`);
        console.log(`   Progress Tracking: ${dataResults.hasProgress ? '✅' : '❌'}`);
        console.log(`   AI Insights: ${dataResults.hasAIInsights ? '✅' : '❌'}`);
        console.log(`   API Calls Made: ${dataResults.apiCalls}`);

        // Calculate overall score
        const buttonScore = viewDetailsResults.buttonsFound > 0 ?
                          (viewDetailsResults.detailsDisplayed / viewDetailsResults.buttonsFound) * 100 : 0;

        const dataScore = [dataResults.hasGoals, dataResults.hasActionSteps,
                          dataResults.hasProgress, dataResults.hasAIInsights]
                         .filter(Boolean).length * 25;

        const overallScore = (buttonScore + dataScore) / 2;

        console.log(`\n🎯 Overall Functionality Score: ${overallScore.toFixed(1)}%`);

        // Generate recommendations
        console.log('\n💡 Recommendations:');
        if (viewDetailsResults.buttonsFound === 0) {
            console.log('   • Add View Details buttons to wellness goals');
        }
        if (viewDetailsResults.buttonsWorking < viewDetailsResults.buttonsFound) {
            console.log('   • Fix non-functional View Details buttons');
        }
        if (!dataResults.hasGoals) {
            console.log('   • Implement wellness goal data display');
        }
        if (!dataResults.hasActionSteps) {
            console.log('   • Add action steps to wellness plans');
        }
        if (!dataResults.hasProgress) {
            console.log('   • Implement progress tracking display');
        }
        if (dataResults.apiCalls === 0) {
            console.log('   • Connect View Details to actual wellness data APIs');
        }

        return {
            viewDetailsResults,
            dataResults,
            overallScore,
            recommendations: this.generateRecommendations(viewDetailsResults, dataResults)
        };
    }

    generateRecommendations(viewResults, dataResults) {
        const recommendations = [];

        if (viewResults.buttonsFound === 0) {
            recommendations.push({
                priority: 'HIGH',
                issue: 'No View Details buttons found',
                solution: 'Add View Details buttons to all wellness goals and milestones'
            });
        }

        if (viewResults.detailsDisplayed < viewResults.buttonsFound) {
            recommendations.push({
                priority: 'HIGH',
                issue: 'View Details buttons not working',
                solution: 'Fix button click handlers and detail modal rendering'
            });
        }

        if (!dataResults.hasGoals) {
            recommendations.push({
                priority: 'MEDIUM',
                issue: 'No wellness goal data displayed',
                solution: 'Implement wellness goal data structure and display'
            });
        }

        if (dataResults.apiCalls === 0) {
            recommendations.push({
                priority: 'HIGH',
                issue: 'No API integration detected',
                solution: 'Connect wellness data to backend APIs'
            });
        }

        return recommendations;
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
            console.log('🧹 Browser closed');
        }
    }

    async runFullTest() {
        try {
            await this.setup();

            const results = {
                navigationSuccess: await this.navigateToWellnessPage(),
                planGenerated: await this.testWellnessPlanGeneration(),
                viewDetailsTest: await this.testViewDetailsButtons(),
                dataIntegrationTest: await this.testWellnessDataIntegration()
            };

            const report = await this.generateTestReport(results);

            // Save detailed report
            const fs = require('fs');
            fs.writeFileSync('view_details_test_report.json', JSON.stringify({
                timestamp: new Date().toISOString(),
                results,
                report
            }, null, 2));

            console.log('\n📄 Detailed report saved to: view_details_test_report.json');

            return report;

        } catch (error) {
            console.log('❌ Test execution failed:', error.message);
            throw error;
        } finally {
            await this.cleanup();
        }
    }
}

// Run the test
async function main() {
    const tester = new ViewDetailsTester();

    try {
        console.log('🧪 STARTING COMPREHENSIVE VIEW DETAILS FUNCTIONALITY TEST');
        console.log('=' * 60);

        const report = await tester.runFullTest();

        if (report.overallScore >= 80) {
            console.log('\n✅ View Details functionality is working well');
        } else if (report.overallScore >= 60) {
            console.log('\n⚠️  View Details functionality has some issues');
        } else {
            console.log('\n❌ View Details functionality needs significant improvement');
        }

        process.exit(report.overallScore >= 60 ? 0 : 1);

    } catch (error) {
        console.log('💥 Test failed:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = ViewDetailsTester;
