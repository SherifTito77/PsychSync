import React, { useState, useEffect } from "react";

interface TeamMember {
  id: number;
  name: string;
  role: string;
  compatibilityScore?: number;
}

const TeamOptimizer: React.FC = () => {
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    // Example fetch
    fetch("/api/v1/team_optimization")
      .then((res) => res.json())
      .then((data) => setTeam(data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <div>
      <h2>Team Optimizer</h2>
      <ul>
        {team.map((item: TeamMember, i: number) => (
          <li key={item.id || i}>
            {item.name} — {item.role} ({item.compatibilityScore ?? "N/A"})
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TeamOptimizer;
