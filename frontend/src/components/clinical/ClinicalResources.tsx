import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface Therapist {
  id: string;
  name: string;
  credentials: string[];
  specializations: string[];
  languages: string[];
  telehealth: boolean;
  insurance: string[];
  rating: number;
  distance?: string;
  consultation_fee?: string;
  availability: string;
}

interface SupportGroup {
  id: string;
  name: string;
  description: string;
  category: string;
  meeting_type: string;
  day: string;
  time: string;
  location: string;
  cost: string;
}

interface Resource {
  id: string;
  title: string;
  description: string;
  category: string;
  type: 'app' | 'website' | 'book' | 'toolkit';
  url?: string;
  download_count?: number;
  rating: number;
  free: boolean;
}

const ClinicalResources: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'therapists' | 'groups' | 'resources'>('therapists');
  const [therapists, setTherapists] = useState<Therapist[]>([]);
  const [supportGroups, setSupportGroups] = useState<SupportGroup[]>([]);
  const [resources, setResources] = useState<Resource[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock data for demonstration - in production this would fetch from API
    const mockTherapists: Therapist[] = [
      {
        id: '1',
        name: 'Dr. Sarah Johnson',
        credentials: ['PhD', 'LCSW'],
        specializations: ['Anxiety', 'Depression', 'Trauma'],
        languages: ['English', 'Spanish'],
        telehealth: true,
        insurance: ['Blue Cross Blue Shield', 'Aetna', 'United Healthcare'],
        rating: 4.8,
        distance: '2.5 miles',
        consultation_fee: '$150-200',
        availability: 'Available this week'
      },
      {
        id: '2',
        name: 'Dr. Michael Chen',
        credentials: ['MD', 'Psychiatrist'],
        specializations: ['Bipolar Disorder', 'Schizophrenia', 'ADHD'],
        languages: ['English', 'Mandarin', 'Cantonese'],
        telehealth: true,
        insurance: ['Medicare', 'Cigna', 'Humana'],
        rating: 4.9,
        distance: '1.8 miles',
        consultation_fee: '$200-300',
        availability: 'Available tomorrow'
      },
      {
        id: '3',
        name: 'Lisa Rodriguez, LMFT',
        credentials: ['MA', 'LMFT'],
        specializations: ['Couples Therapy', 'Family Therapy', 'Individual Therapy'],
        languages: ['English', 'Spanish'],
        telehealth: false,
        insurance: ['Blue Cross Blue Shield', 'Kaiser Permanente'],
        rating: 4.7,
        distance: '3.2 miles',
        consultation_fee: '$120-180',
        availability: 'Next week'
      },
      {
        id: '4',
        name: 'Dr. James Williams',
        credentials: ['PsyD', 'Clinical Psychologist'],
        specializations: ['PTSD', 'OCD', 'Anxiety Disorders'],
        languages: ['English'],
        telehealth: true,
        insurance: ['Aetna', 'Cigna', 'United Healthcare'],
        rating: 4.6,
        distance: '4.1 miles',
        consultation_fee: '$140-190',
        availability: 'Available in 2 weeks'
      }
    ];

    const mockSupportGroups: SupportGroup[] = [
      {
        id: '1',
        name: 'Anxiety Support Group',
        description: 'Peer support for managing anxiety symptoms and sharing coping strategies',
        category: 'Anxiety',
        meeting_type: 'In-person',
        day: 'Tuesday',
        time: '6:00 PM',
        location: 'Downtown Mental Health Center',
        cost: 'Free'
      },
      {
        id: '2',
        name: 'Depression Recovery Circle',
        description: 'Supportive environment for individuals managing depression',
        category: 'Depression',
        meeting_type: 'Virtual',
        day: 'Thursday',
        time: '7:30 PM',
        location: 'Zoom',
        cost: 'Free'
      },
      {
        id: '3',
        name: 'LGBTQ+ Mental Health Support',
        description: 'Safe space for LGBTQ+ individuals to discuss mental health',
        category: 'LGBTQ+',
        meeting_type: 'Hybrid',
        day: 'Monday',
        time: '5:30 PM',
        location: 'Community Center',
        cost: 'Free'
      },
      {
        id: '4',
        name: 'Caregivers Support Network',
        description: 'Support for family members and caregivers of those with mental illness',
        category: 'Caregivers',
        meeting_type: 'In-person',
        day: 'Wednesday',
        time: '6:00 PM',
        location: 'Senior Center',
        cost: 'Free'
      }
    ];

    const mockResources: Resource[] = [
      {
        id: '1',
        title: 'Calm - Meditation and Sleep',
        description: 'Guided meditation, breathing exercises, and sleep stories for better mental health',
        category: 'Meditation',
        type: 'app',
        rating: 4.7,
        free: false
      },
      {
        id: '2',
        title: 'Moodpath - Depression & Anxiety',
        description: 'CBT-based activities and tools for managing depression and anxiety',
        category: 'Self-Help',
        type: 'app',
        rating: 4.6,
        free: true
      },
      {
        id: '3',
        title: 'PTSD Coach',
        description: 'Self-help app for managing PTSD symptoms with evidence-based techniques',
        category: 'Trauma',
        type: 'app',
        rating: 4.4,
        free: true
      },
      {
        id: '4',
        'title': 'Seven Cups - 24/7 Emotional Support',
        description: 'Connect with trained listeners for emotional support anytime',
        category: 'Crisis Support',
        type: 'app',
        rating: 4.3,
        free: true
      }
    ];

    setTherapists(mockTherapists);
    setSupportGroups(mockSupportGroups);
    setResources(mockResources);
    setLoading(false);
  }, []);

  const filteredTherapists = therapists.filter(therapist =>
    therapist.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    therapist.specializations.some(spec => spec.toLowerCase().includes(searchTerm.toLowerCase())) ||
    therapist.languages.some(lang => lang.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const filteredGroups = supportGroups.filter(group =>
    group.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    group.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    group.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredResources = resources.filter(resource =>
    resource.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    resource.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    resource.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <span key={i} className={i < Math.floor(rating) ? 'text-yellow-400' : 'text-gray-300'}>
        ★
      </span>
    ));
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading clinical resources...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Clinical Resources</h1>
        <p className="text-gray-600">
          Find therapists, support groups, and evidence-based mental health resources to support your wellness journey.
        </p>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="max-w-md">
          <input
            type="text"
            placeholder="Search therapists, groups, or resources..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('therapists')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'therapists'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Therapists ({filteredTherapists.length})
          </button>
          <button
            onClick={() => setActiveTab('groups')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'groups'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Support Groups ({filteredGroups.length})
          </button>
          <button
            onClick={() => setActiveTab('resources')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'resources'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Resources & Tools ({filteredResources.length})
          </button>
        </nav>
      </div>

      {/* Therapists Tab */}
      {activeTab === 'therapists' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredTherapists.map((therapist) => (
            <Card key={therapist.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-xl">{therapist.name}</CardTitle>
                    <p className="text-sm text-gray-600">
                      {therapist.credentials.join(', ')}
                    </p>
                    <div className="flex items-center mt-1">
                      {renderStars(therapist.rating)}
                      <span className="ml-2 text-sm text-gray-600">({therapist.rating})</span>
                    </div>
                  </div>
                  <div className="text-right">
                    {therapist.telehealth && (
                      <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                        Telehealth Available
                      </span>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <h4 className="font-semibold text-sm text-gray-900">Specializations</h4>
                    <div className="flex flex-wrap gap-2">
                      {therapist.specializations.map((spec, index) => (
                        <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                          {spec}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <h4 className="font-semibold text-gray-900">Languages</h4>
                      <p>{therapist.languages.join(', ')}</p>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">Insurance</h4>
                      <p className="text-xs">{therapist.insurance.slice(0, 2).join(', ')}...</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <h4 className="font-semibold text-gray-900">Distance</h4>
                      <p>{therapist.distance}</p>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">Consultation Fee</h4>
                      <p>{therapist.consultation_fee}</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-green-600">{therapist.availability}</span>
                    <Button size="sm" variant="outline">
                      Contact
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Support Groups Tab */}
      {activeTab === 'groups' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredGroups.map((group) => (
            <Card key={group.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <CardTitle className="text-xl">{group.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <p className="text-gray-600">{group.description}</p>

                  <div className="flex flex-wrap gap-2">
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                      {group.category}
                    </span>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      {group.meeting_type}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <h4 className="font-semibold text-gray-900">Schedule</h4>
                      <p>{group.day} at {group.time}</p>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">Location</h4>
                      <p>{group.location}</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-green-600 font-medium">{group.cost}</span>
                    <Button size="sm" variant="primary">
                      Join Group
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Resources Tab */}
      {activeTab === 'resources' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredResources.map((resource) => (
            <Card key={resource.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">{resource.title}</CardTitle>
                  <div className="text-right">
                    {resource.free && (
                      <span className="inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                        Free
                      </span>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <p className="text-sm text-gray-600">{resource.description}</p>

                  <div className="flex items-center justify-between">
                    <div>
                      <span className="inline-block px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                        {resource.category}
                      </span>
                      <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded ml-2">
                        {resource.type}
                      </span>
                    </div>
                    <div className="flex items-center">
                      {renderStars(resource.rating)}
                      <span className="ml-2 text-sm text-gray-600">({resource.rating})</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    {resource.type === 'app' ? (
                      <span className="text-sm text-gray-500">Mobile app</span>
                    ) : (
                      <span className="text-sm text-gray-500">Web resource</span>
                    )}
                    <Button size="sm" variant="outline">
                      View Details
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Emergency Contact Banner */}
      <Card className="mt-8 bg-red-50 border-red-200">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-red-800">In Crisis? Get Immediate Help</h3>
              <p className="text-red-600 mt-1">
                If you're experiencing thoughts of self-harm or suicide, please reach out immediately.
              </p>
            </div>
            <div className="space-y-2">
              <Button variant="primary" className="bg-red-600 hover:bg-red-700">
                Call 988
              </Button>
              <Button variant="outline" className="text-red-600 border-red-300 hover:bg-red-100">
                Text HOME to 741741
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ClinicalResources;
