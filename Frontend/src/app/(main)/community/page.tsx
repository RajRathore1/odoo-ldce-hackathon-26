import { CommunityFeed } from "@/components/community-feed";

export default function CommunityPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-heading text-3xl font-semibold sm:text-4xl">
          Community
        </h1>
        <p className="mt-2 max-w-xl text-text-muted">
          Trip notes and tips from other GlobeTrotters, straight from the
          road.
        </p>
      </div>

      <CommunityFeed />
    </div>
  );
}
