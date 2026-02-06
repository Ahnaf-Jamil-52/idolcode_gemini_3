import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { ArrowLeft } from 'lucide-react';

export const Profile = () => {
  const { handle } = useParams();
  const navigate = useNavigate();

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Pattern - Same as home page */}
      <div className="absolute inset-0 grid-pattern opacity-30"></div>
      <div className="absolute inset-0 hero-pattern"></div>
      
      {/* Background Image */}
      <div 
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: 'url(https://static.prod-images.emergentagent.com/jobs/6100a3e9-50bd-415e-b52f-278e95a062af/images/71b7ee53dbcb65c9a063c355a5bb8e84ec9d2c333281422177e917d3926a5bae.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      ></div>

      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="glass-card p-8 rounded-3xl border border-border">
          {/* Back Button */}
          <Button
            onClick={() => navigate('/')}
            variant="ghost"
            className="mb-6 hover:bg-primary/10"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>

          {/* Profile Content */}
          <div className="text-center space-y-6">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-r from-primary/30 to-accent/30 border-2 border-primary/50">
              <span className="text-4xl font-bold text-primary">
                {handle ? handle[0].toUpperCase() : 'P'}
              </span>
            </div>

            <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-cyan-300 to-purple-400 bg-clip-text text-transparent">
              {handle ? `${handle}'s Profile` : 'Profile Page'}
            </h1>

            <p className="text-lg text-muted-foreground">
              Profile page coming soon...
            </p>

            <div className="pt-4">
              <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full glass-card border border-primary/30">
                <span className="text-sm text-muted-foreground">
                  Selected Coding Idol: <span className="text-primary font-semibold">{handle || 'None'}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Profile;
