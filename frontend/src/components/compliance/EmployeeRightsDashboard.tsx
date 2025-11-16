import React, { useState, useEffect } from 'react';
import {
  Shield,
  BookOpen,
  Users,
  AlertTriangle,
  Phone,
  Mail,
  ExternalLink,
  Search,
  Map,
  HelpCircle,
  Download,
  ChevronDown,
  ChevronRight,
  Flag,
  Scale,
  Building,
  UserCheck,
  Clock,
  DollarSign,
  Heart
} from 'lucide-react';
import { useNotification } from '../../contexts/NotificationContext';
import { complianceService } from '../../services/complianceService';
import { EmployeeRights } from '../../types/compliance';
import { Button } from '../common/Button';
import { Card } from '../common/card';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
interface EmployeeRightsDashboardProps {
  className?: string;
}
interface StateData {
  minimum_wage: string;
  additional_protections: string[];
  state_agency: {
    name: string;
    phone: string;
    website: string;
  };
}
export const EmployeeRightsDashboard: React.FC<EmployeeRightsDashboardProps> = ({ className = '' }) => {
  const [rights, setRights] = useState<EmployeeRights | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('overview');
  const [userState, setUserState] = useState<string>('');
  const [industry, setIndustry] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));
  const { showNotification } = useNotification();
  useEffect(() => {
    loadRights();
  }, [userState, industry]);
  const loadRights = async () => {
    try {
      setLoading(true);
      const data = await complianceService.getEmployeeRights(userState, industry);
      setRights(data);
    } catch (error) {
      console.error('Failed to load employee rights:', error);
      showNotification('Failed to load employee rights information', 'error');
    } finally {
      setLoading(false);
    }
  };
  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };
  const downloadRightsGuide = async () => {
    try {
      const response = await fetch('/api/v1/reports/employee-rights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ state: userState, industry })
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `employee-rights-guide-${userState || 'federal'}-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showNotification('Rights guide downloaded successfully', 'success');
      }
    } catch (error) {
      showNotification('Failed to download rights guide', 'error');
    }
  };
  if (loading) {
    return <LoadingSpinner />;
  }
  if (!rights) {
    return (
      <Card>
        <div className="text-center py-8">
          <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Unable to load employee rights information</p>
          <Button onClick={loadRights} className="mt-4">Try Again</Button>
        </div>
      </Card>
    );
  }
  const filteredFAQs = rights.faq.filter(faq =>
    faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
    faq.answer.toLowerCase().includes(searchTerm.toLowerCase())
  );
  return (
    <div className={`max-w-7xl mx-auto p-6 space-y-6 ${className}`}>
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex justify-center mb-4">
          <div className="p-4 bg-indigo-100 rounded-full">
            <Shield className="w-12 h-12 text-indigo-600" />
          </div>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Know Your Rights</h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto">
          Understanding your rights as an employee empowers you to recognize violations
          and seek appropriate recourse. Your rights are protected by federal and state laws.
        </p>
      </div>
      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <QuickActionCard
          description="Submit anonymous feedback about workplace issues"
          icon={<AlertTriangle className="w-8 h-8" />}
          link="/anonymous-feedback"
          color="red"
        />
        <QuickActionCard
          description="Get a printable PDF of your employee rights"
          icon={<Download className="w-8 h-8" />}
          onClick={downloadRightsGuide}
          color="blue"
        />
        <QuickActionCard
          description="Get contact information for regulatory agencies"
          icon={<Phone className="w-8 h-8" />}
          link="/reporting-guidelines"
          color="green"
        />
      </div>
      {/* State and Industry Selection */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Map className="w-4 h-4 inline mr-1" />
              Select Your State
            </label>
            <select
              value={userState}
              onChange={(e) => setUserState(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Federal Rights Only</option>
              <option value="AL">Alabama</option>
              <option value="AK">Alaska</option>
              <option value="AZ">Arizona</option>
              <option value="AR">Arkansas</option>
              <option value="CA">California</option>
              <option value="CO">Colorado</option>
              <option value="CT">Connecticut</option>
              <option value="DE">Delaware</option>
              <option value="FL">Florida</option>
              <option value="GA">Georgia</option>
              <option value="HI">Hawaii</option>
              <option value="ID">Idaho</option>
              <option value="IL">Illinois</option>
              <option value="IN">Indiana</option>
              <option value="IA">Iowa</option>
              <option value="KS">Kansas</option>
              <option value="KY">Kentucky</option>
              <option value="LA">Louisiana</option>
              <option value="ME">Maine</option>
              <option value="MD">Maryland</option>
              <option value="MA">Massachusetts</option>
              <option value="MI">Michigan</option>
              <option value="MN">Minnesota</option>
              <option value="MS">Mississippi</option>
              <option value="MO">Missouri</option>
              <option value="MT">Montana</option>
              <option value="NE">Nebraska</option>
              <option value="NV">Nevada</option>
              <option value="NH">New Hampshire</option>
              <option value="NJ">New Jersey</option>
              <option value="NM">New Mexico</option>
              <option value="NY">New York</option>
              <option value="NC">North Carolina</option>
              <option value="ND">North Dakota</option>
              <option value="OH">Ohio</option>
              <option value="OK">Oklahoma</option>
              <option value="OR">Oregon</option>
              <option value="PA">Pennsylvania</option>
              <option value="RI">Rhode Island</option>
              <option value="SC">South Carolina</option>
              <option value="SD">South Dakota</option>
              <option value="TN">Tennessee</option>
              <option value="TX">Texas</option>
              <option value="UT">Utah</option>
              <option value="VT">Vermont</option>
              <option value="VA">Virginia</option>
              <option value="WA">Washington</option>
              <option value="WV">West Virginia</option>
              <option value="WI">Wisconsin</option>
              <option value="WY">Wyoming</option>
            </select>
            {userState && (
              <p className="text-sm text-gray-600 mt-2">
                Showing {userState} specific protections in addition to federal rights
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Building className="w-4 h-4 inline mr-1" />
              Industry (Optional)
            </label>
            <select
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Industries</option>
              <option value="healthcare">Healthcare</option>
              <option value="construction">Construction</option>
              <option value="retail">Retail</option>
              <option value="manufacturing">Manufacturing</option>
              <option value="technology">Technology</option>
              <option value="hospitality">Hospitality</option>
              <option value="transportation">Transportation</option>
              <option value="education">Education</option>
            </select>
            {industry && (
              <p className="text-sm text-gray-600 mt-2">
                Showing industry-specific protections
              </p>
            )}
          </div>
        </div>
      </Card>
      {/* Federal Rights Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(rights.federal_rights).map(([key, category]: [string, any]) => (
          <RightsCategoryCard
            key={key}
            title={category.title}
            description={getCategoryDescription(key)}
            icon={getCategoryIcon(key)}
            onClick={() => setSelectedCategory(key)}
            isExpanded={selectedCategory === key}
            color={getCategoryColor(key)}
          />
        ))}
      </div>
      {/* Selected Category Detail */}
      {selectedCategory !== 'overview' && selectedCategory in rights.federal_rights && (
        <Card>
          <RightsCategoryDetail
            category={rights.federal_rights[selectedCategory]}
            categoryName={selectedCategory}
          />
        </Card>
      )}
      {/* State-Specific Rights */}
      {userState && rights.state_rights && Object.keys(rights.state_rights).length > 0 && (
        <Card className="border-blue-200 bg-blue-50">
          <div className="flex items-center mb-4">
            <Map className="w-6 h-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold text-blue-900">
              {userState} State-Specific Rights
            </h2>
          </div>
          <StateRightsContent stateData={rights.state_rights} />
        </Card>
      )}
      {/* Reporting Resources */}
      <Card>
        <div className="flex items-center mb-6">
          <Phone className="w-6 h-6 text-green-600 mr-2" />
          <h2 className="text-xl font-semibold">How to Report Violations</h2>
        </div>
        <ReportingResourcesGrid resources={rights.how_to_report} />
      </Card>
      {/* FAQ Section */}
      <Card>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <HelpCircle className="w-6 h-6 text-purple-600 mr-2" />
            <h2 className="text-xl font-semibold">Frequently Asked Questions</h2>
          </div>
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search FAQs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>
        <FAQAccordion faqs={filteredFAQs} />
      </Card>
      {/* Emergency Contacts */}
      <Card className="border-red-200 bg-red-50">
        <div className="flex items-center mb-4">
          <AlertTriangle className="w-6 h-6 text-red-600 mr-2" />
          <h2 className="text-xl font-semibold text-red-900">Emergency Contacts</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <EmergencyContactCard
            phone="1-800-321-6742"
            description="Workplace safety and health violations"
          />
          <EmergencyContactCard
            phone="1-800-669-4000"
            description="Discrimination and harassment"
          />
          <EmergencyContactCard
            phone="1-866-487-2365"
            description="Wage theft, overtime, minimum wage"
          />
          <EmergencyContactCard
            phone="1-844-762-6572"
            description="Union rights and unfair labor practices"
          />
        </div>
      </Card>
    </div>
  );
};
// Helper Components and Functions
interface QuickActionCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  link?: string;
  onClick?: () => void;
  color: 'red' | 'blue' | 'green' | 'yellow' | 'purple';
}
const QuickActionCard: React.FC<QuickActionCardProps> = ({
  title,
  description,
  icon,
  link,
  onClick,
  color
}) => {
  const getColorClasses = (color: string) => {
    const colors = {
      red: 'text-red-600 hover:bg-red-50 border-red-200',
      blue: 'text-blue-600 hover:bg-blue-50 border-blue-200',
      green: 'text-green-600 hover:bg-green-50 border-green-200',
      yellow: 'text-yellow-600 hover:bg-yellow-50 border-yellow-200',
      purple: 'text-purple-600 hover:bg-purple-50 border-purple-200'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };
  const content = (
    <>
      <div className="text-center mb-3">
        {icon}
      </div>
      <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </>
  );
  const cardClasses = `block p-6 rounded-lg border transition-all duration-200 ${getColorClasses(color)}`;
  if (link) {
    return (
      <a href={link} className={cardClasses}>
        {content}
      </a>
    );
  }
  return (
    <button onClick={onClick} className={cardClasses}>
      {content}
    </button>
  );
};
interface RightsCategoryCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  onClick: () => void;
  isExpanded: boolean;
  color: 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'orange';
}
const RightsCategoryCard: React.FC<RightsCategoryCardProps> = ({
  title,
  description,
  icon,
  onClick,
  isExpanded,
  color
}) => {
  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-100 text-blue-600 hover:bg-blue-200',
      green: 'bg-green-100 text-green-600 hover:bg-green-200',
      yellow: 'bg-yellow-100 text-yellow-600 hover:bg-yellow-200',
      red: 'bg-red-100 text-red-600 hover:bg-red-200',
      purple: 'bg-purple-100 text-purple-600 hover:bg-purple-200',
      orange: 'bg-orange-100 text-orange-600 hover:bg-orange-200'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };
  return (
    <button
      onClick={onClick}
      className={`w-full p-6 rounded-lg border transition-all duration-200 ${
        isExpanded ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md'
      }`}
    >
      <div className="flex items-start space-x-4">
        <div className={`p-3 rounded-lg ${getColorClasses(color)}`}>
          {icon}
        </div>
        <div className="text-left flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
        <ChevronRight className={`w-5 h-5 text-gray-400 transform transition-transform ${
          isExpanded ? 'rotate-90' : ''
        }`} />
      </div>
    </button>
  );
};
const getCategoryDescription = (key: string): string => {
  const descriptions: Record<string, string> = {
    wage_and_hour: 'Minimum wage, overtime, and pay protections',
    discrimination: 'Protection from discrimination and harassment',
    harassment: 'Freedom from workplace harassment',
    safety: 'Safe working conditions and OSHA protections',
    leave: 'Family, medical, and personal leave rights',
    organizing: 'Rights to organize and collective bargaining',
    whistleblower: 'Protection for reporting violations',
    privacy: 'Workplace privacy and personnel file rights',
    retaliation: 'Protection from retaliation for exercising rights'
  };
  return descriptions[key] || '';
};
const getCategoryIcon = (key: string) => {
  const icons: Record<string, React.ReactNode> = {
    wage_and_hour: <DollarSign className="w-6 h-6" />,
    discrimination: <Users className="w-6 h-6" />,
    harassment: <AlertTriangle className="w-6 h-6" />,
    safety: <Shield className="w-6 h-6" />,
    leave: <Clock className="w-6 h-6" />,
    organizing: <Users className="w-6 h-6" />,
    whistleblower: <Flag className="w-6 h-6" />,
    privacy: <UserCheck className="w-6 h-6" />,
    retaliation: <Scale className="w-6 h-6" />
  };
  return icons[key] || <BookOpen className="w-6 h-6" />;
};
const getCategoryColor = (key: string): 'blue' | 'green' | 'yellow' | 'red' | 'purple' | 'orange' => {
  const colors: Record<string, any> = {
    wage_and_hour: 'green',
    discrimination: 'red',
    harassment: 'orange',
    safety: 'yellow',
    leave: 'blue',
    organizing: 'purple',
    whistleblower: 'red',
    privacy: 'blue',
    retaliation: 'purple'
  };
  return colors[key] || 'blue';
};
const RightsCategoryDetail: React.FC<{ category: any; categoryName: string }> = ({ category, categoryName }) => {
  const [expandedRight, setExpandedRight] = useState<number | null>(null);
  return (
    <div>
      <h3 className="text-xl font-semibold mb-4">{category.title}</h3>
      {category.rights && (
        <div className="space-y-4 mb-6">
          <h4 className="font-semibold text-gray-900">Your Rights Include:</h4>
          {category.rights.map((right: any, index: number) => (
            <div key={index} className="border rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <h5 className="font-medium text-gray-900">{right.right}</h5>
                <button
                  onClick={() => setExpandedRight(expandedRight === index ? null : index)}
                  className="text-blue-600 hover:text-blue-700"
                >
                  {expandedRight === index ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-sm text-gray-600">{right.description}</p>
              {right.law && (
                <p className="text-xs text-gray-500 mt-2">Law: {right.law}</p>
              )}
              {expandedRight === index && (
                <div className="mt-3 pt-3 border-t text-sm text-gray-600">
                  {right.enforcement && <p><strong>Enforcement:</strong> {right.enforcement}</p>}
                  {right.how_to_report && <p><strong>How to Report:</strong> {right.how_to_report}</p>}
                  {right.contact && <p><strong>Contact:</strong> {right.contact}</p>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      {category.protected_classes && (
        <div className="mb-6">
          <h4 className="font-semibold text-gray-900 mb-2">Protected Classes:</h4>
          <div className="flex flex-wrap gap-2">
            {category.protected_classes.map((cls: string, index: number) => (
              <Badge key={index} color="blue" variant="outline" size="sm">
                {cls}
              </Badge>
            ))}
          </div>
        </div>
      )}
      {category.protected_activities && (
        <div className="mb-6">
          <h4 className="font-semibold text-gray-900 mb-2">Protected Activities:</h4>
          <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
            {category.protected_activities.map((activity: string, index: number) => (
              <li key={index}>{activity}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
const StateRightsContent: React.FC<{ stateData: StateData }> = ({ stateData }) => {
  return (
    <div className="space-y-4">
      {stateData.minimum_wage && (
        <div className="flex items-center justify-between">
          <span className="font-medium">State Minimum Wage:</span>
          <span className="font-semibold text-green-600">{stateData.minimum_wage}</span>
        </div>
      )}
      {stateData.additional_protections && stateData.additional_protections.length > 0 && (
        <div>
          <h4 className="font-medium mb-2">Additional State Protections:</h4>
          <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
            {stateData.additional_protections.map((protection: string, index: number) => (
              <li key={index}>{protection}</li>
            ))}
          </ul>
        </div>
      )}
      {stateData.state_agency && (
        <div className="bg-white p-4 rounded-lg border">
          <h4 className="font-medium mb-2">State Labor Agency:</h4>
          <div className="text-sm space-y-1">
            <p><strong>{stateData.state_agency.name}</strong></p>
            <div className="flex items-center space-x-4">
              <span className="flex items-center">
                <Phone className="w-3 h-3 mr-1" />
                {stateData.state_agency.phone}
              </span>
              <a
                href={stateData.state_agency.website}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center text-blue-600 hover:text-blue-700"
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                Website
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
const ReportingResourcesGrid: React.FC<{ resources: any }> = ({ resources }) => {
  if (!resources?.federal_agencies) return null;
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {resources.federal_agencies.map((agency: any, index: number) => (
        <div key={index} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
          <h4 className="font-semibold text-gray-900 mb-2">{agency.name}</h4>
          <p className="text-sm text-gray-600 mb-3">{agency.handles.join(', ')}</p>
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-3">
              <span className="flex items-center">
                <Phone className="w-3 h-3 mr-1" />
                {agency.phone}
              </span>
              {agency.tty && (
                <span className="text-gray-500">TTY: {agency.tty}</span>
              )}
            </div>
            <a
              href={agency.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-700"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      ))}
    </div>
  );
};
const FAQAccordion: React.FC<{ faqs: Array<{ question: string; answer: string }> }> = ({ faqs }) => {
  const [expandedQuestion, setExpandedQuestion] = useState<number | null>(null);
  return (
    <div className="space-y-4">
      {faqs.map((faq, index) => (
        <div key={index} className="border rounded-lg">
          <button
            onClick={() => setExpandedQuestion(expandedQuestion === index ? null : index)}
            className="w-full text-left p-4 hover:bg-gray-50 focus:outline-none focus:bg-gray-50"
          >
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-gray-900">{faq.question}</h4>
              <ChevronDown
                className={`w-5 h-5 text-gray-400 transform transition-transform ${
                  expandedQuestion === index ? 'rotate-180' : ''
                }`}
              />
            </div>
          </button>
          {expandedQuestion === index && (
            <div className="px-4 pb-4 text-sm text-gray-600">
              {faq.answer}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
const EmergencyContactCard: React.FC<{
  title: string;
  phone: string;
  description: string;
}> = ({ title, phone, description }) => {
  return (
    <div className="bg-white p-4 rounded-lg border">
      <h4 className="font-semibold text-gray-900 mb-1">{title}</h4>
      <p className="text-sm text-gray-600 mb-2">{description}</p>
      <a
        href={`tel:${phone}`}
        className="inline-flex items-center text-red-600 hover:text-red-700 font-medium"
      >
        <Phone className="w-4 h-4 mr-1" />
        {phone}
      </a>
    </div>
  );
};