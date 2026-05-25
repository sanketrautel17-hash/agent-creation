import { Link } from "react-router-dom";

export default function AgentCard({ title, description, agentId }) {
  return (
    <article className="card">
      <h3>{title}</h3>
      <p>{description}</p>
      <Link className="primary-button" to={`/agents/${agentId}`}>
        Inspect agent
      </Link>
    </article>
  );
}
