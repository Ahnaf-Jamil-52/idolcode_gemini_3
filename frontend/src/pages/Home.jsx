import React from 'react';
import Navbar from '../components/Navbar';
import HeroSection from '../components/HeroSection';
import FeaturesSection from '../components/FeaturesSection';
import HowItWorks from '../components/HowItWorks';
import StatsSection from '../components/StatsSection';
import TestimonialsSection from '../components/TestimonialsSection';
import PricingSection from '../components/PricingSection';
import FAQSection from '../components/FAQSection';
import CTASection from '../components/CTASection';
import Footer from '../components/Footer';

export const Home = () => {
  return (
    <>
      <Navbar />
      <HeroSection />
      <StatsSection />
      <FeaturesSection />
      <HowItWorks />
      <TestimonialsSection />
      <PricingSection />
      <FAQSection />
      <CTASection />
      <Footer />
    </>
  );
};

export default Home;
