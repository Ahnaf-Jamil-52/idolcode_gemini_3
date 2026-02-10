import React from 'react';
import Navbar from '../components/Navbar';
import HeroSection from '../components/HeroSection';
import FeaturesSection from '../components/FeaturesSection';
import HowItWorks from '../components/HowItWorks';
import FAQSection from '../components/FAQSection';
import CTASection from '../components/CTASection';
import ComingSoonSection from '../components/ComingSoonSection';
import VSCodeExtensionSection from '../components/VSCodeExtensionSection';
import Footer from '../components/Footer';

export const Home = () => {
  return (
    <>
      <Navbar />
      <HeroSection />
      <FeaturesSection />
      <HowItWorks />
      <ComingSoonSection />
      <VSCodeExtensionSection />
      <FAQSection />
      <CTASection />
      <Footer />
    </>
  );
};

export default Home;
