const companyHRQuestions = [
    {
      company: "Amazon",
      questions: [
        {
          question: "Tell me about a time you took ownership.",
          answer: "Describe a project where you went beyond your role, took responsibility, and ensured completion despite obstacles."
        },
        {
          question: "Tell me about a time you failed.",
          answer: "Explain a real failure, what caused it, what you learned, and how you improved afterward."
        },
        {
          question: "Describe a difficult customer interaction.",
          answer: "Explain how you handled a demanding user, stayed calm, and delivered a solution."
        },
        {
          question: "Tell me about a time you worked under pressure.",
          answer: "Mention deadlines, prioritization, and how you maintained quality."
        },
        {
          question: "Tell me about a time you disagreed with your team.",
          answer: "Explain your viewpoint, how you communicated respectfully, and final resolution."
        },
        {
          question: "Describe a time you made a decision without full data.",
          answer: "Focus on judgment, risk-taking, and outcome."
        },
        {
          question: "Tell me about a time you improved a process.",
          answer: "Show measurable impact (time saved, efficiency improved)."
        },
        {
          question: "Tell me about a time you handled conflict.",
          answer: "Explain mediation, understanding both sides, and resolution."
        },
        {
          question: "Why Amazon?",
          answer: "Talk about leadership principles, scale, and customer obsession."
        },
        {
          question: "Tell me about a time you delivered results.",
          answer: "Highlight outcome, impact, and metrics."
        }
      ]
    },
  
    {
      company: "Google",
      questions: [
        {
          question: "Tell me about yourself.",
          answer: "Brief background → key skills → current focus → why relevant to role."
        },
        {
          question: "Describe a challenging problem you solved.",
          answer: "Explain complexity, approach, and final solution."
        },
        {
          question: "How do you handle ambiguity?",
          answer: "Talk about breaking problems into smaller parts and experimenting."
        },
        {
          question: "Tell me about a time you showed leadership.",
          answer: "Mention initiative, guiding team, and results."
        },
        {
          question: "Why Google?",
          answer: "Focus on innovation, impact, and learning culture."
        },
        {
          question: "Tell me about a time you learned something quickly.",
          answer: "Show adaptability and curiosity."
        },
        {
          question: "Describe a time you worked in a team.",
          answer: "Focus on collaboration and contribution."
        },
        {
          question: "Tell me about a failure.",
          answer: "Highlight learning and growth."
        },
        {
          question: "How do you prioritize tasks?",
          answer: "Explain logic (impact vs urgency)."
        },
        {
          question: "Tell me about a time you solved a complex problem.",
          answer: "Break down steps and reasoning."
        }
      ]
    },
  
    {
      company: "Microsoft",
      questions: [
        {
          question: "Tell me about a time you worked in a team.",
          answer: "Explain collaboration and your contribution."
        },
        {
          question: "Describe a conflict you resolved.",
          answer: "Focus on communication and compromise."
        },
        {
          question: "Why Microsoft?",
          answer: "Mention products, culture, and growth."
        },
        {
          question: "Tell me about a failure.",
          answer: "Explain lesson learned and improvement."
        },
        {
          question: "How do you prioritize tasks?",
          answer: "Discuss planning and deadlines."
        },
        {
          question: "Tell me about a time you handled pressure.",
          answer: "Explain how you managed workload."
        },
        {
          question: "Describe a leadership experience.",
          answer: "Show initiative and team impact."
        },
        {
          question: "Tell me about a time you solved a problem.",
          answer: "Explain steps and outcome."
        },
        {
          question: "How do you handle feedback?",
          answer: "Show openness and improvement."
        },
        {
          question: "Tell me about a project you’re proud of.",
          answer: "Highlight impact and learning."
        }
      ]
    },

    {
        company: "Meta",
        questions: [
          {
            question: "Tell me about a time you moved fast.",
            answer: "Explain a situation where you delivered quickly without compromising too much on quality."
          },
          {
            question: "Tell me about a time you took initiative.",
            answer: "Show how you identified a problem and solved it without being asked."
          },
          {
            question: "Why Meta?",
            answer: "Talk about impact, scale, and building products used by millions."
          },
          {
            question: "Describe a challenging project.",
            answer: "Explain complexity and how you overcame obstacles."
          },
          {
            question: "Tell me about a time you worked in ambiguity.",
            answer: "Explain how you structured unclear problems."
          },
          {
            question: "Tell me about a conflict in your team.",
            answer: "Focus on resolution and communication."
          },
          {
            question: "How do you handle feedback?",
            answer: "Show openness and improvement."
          },
          {
            question: "Tell me about a time you failed.",
            answer: "Explain learning and growth."
          },
          {
            question: "How do you prioritize work?",
            answer: "Discuss impact vs urgency."
          },
          {
            question: "Tell me about a time you improved something.",
            answer: "Show measurable improvement."
          }
        ]
      },
    
      {
        company: "Apple",
        questions: [
          {
            question: "Why Apple?",
            answer: "Focus on design, innovation, and user experience."
          },
          {
            question: "Tell me about a time you paid attention to detail.",
            answer: "Explain how small details made a big difference."
          },
          {
            question: "Describe a time you handled pressure.",
            answer: "Explain how you maintained quality under deadlines."
          },
          {
            question: "Tell me about a failure.",
            answer: "Highlight learning and improvement."
          },
          {
            question: "Describe a team experience.",
            answer: "Show collaboration and contribution."
          },
          {
            question: "Tell me about a time you solved a problem.",
            answer: "Explain approach and outcome."
          },
          {
            question: "How do you handle feedback?",
            answer: "Show growth mindset."
          },
          {
            question: "Tell me about a project you're proud of.",
            answer: "Highlight impact and quality."
          },
          {
            question: "How do you ensure quality in your work?",
            answer: "Explain processes and checks."
          },
          {
            question: "Tell me about a time you improved a process.",
            answer: "Focus on efficiency gains."
          }
        ]
      },
    
      {
        company: "Netflix",
        questions: [
          {
            question: "Why Netflix?",
            answer: "Talk about freedom & responsibility culture."
          },
          {
            question: "Tell me about a time you took ownership.",
            answer: "Explain accountability and results."
          },
          {
            question: "Describe a time you made a tough decision.",
            answer: "Focus on judgment and outcome."
          },
          {
            question: "Tell me about a failure.",
            answer: "Show learning and accountability."
          },
          {
            question: "How do you handle feedback?",
            answer: "Emphasize honesty and growth."
          },
          {
            question: "Tell me about a time you worked independently.",
            answer: "Show self-direction."
          },
          {
            question: "Describe a challenging project.",
            answer: "Explain complexity and solution."
          },
          {
            question: "How do you prioritize tasks?",
            answer: "Discuss impact-driven decisions."
          },
          {
            question: "Tell me about a time you disagreed with someone.",
            answer: "Focus on respectful communication."
          },
          {
            question: "Tell me about a time you delivered high impact.",
            answer: "Highlight measurable results."
          }
        ]
      },
    
      {
        company: "TCS",
        questions: [
          {
            question: "Tell me about yourself.",
            answer: "Brief introduction with education and skills."
          },
          {
            question: "Why TCS?",
            answer: "Talk about stability, learning, and growth."
          },
          {
            question: "Describe a team project.",
            answer: "Explain your role and contribution."
          },
          {
            question: "Tell me about a challenge you faced.",
            answer: "Explain problem and solution."
          },
          {
            question: "How do you handle pressure?",
            answer: "Talk about time management."
          },
          {
            question: "Tell me about your strengths.",
            answer: "Relate strengths to role."
          },
          {
            question: "Tell me about your weaknesses.",
            answer: "Be honest and show improvement."
          },
          {
            question: "Are you willing to relocate?",
            answer: "Show flexibility."
          },
          {
            question: "Tell me about a failure.",
            answer: "Explain lesson learned."
          },
          {
            question: "Where do you see yourself in 5 years?",
            answer: "Show growth and commitment."
          }
        ]
      },
    
      {
        company: "Infosys",
        questions: [
          {
            question: "Tell me about yourself.",
            answer: "Highlight education and skills."
          },
          {
            question: "Why Infosys?",
            answer: "Talk about learning opportunities."
          },
          {
            question: "Describe a project you worked on.",
            answer: "Explain your contribution."
          },
          {
            question: "Tell me about a failure.",
            answer: "Explain learning outcome."
          },
          {
            question: "How do you handle deadlines?",
            answer: "Explain planning and prioritization."
          },
          {
            question: "Tell me about teamwork experience.",
            answer: "Highlight collaboration."
          },
          {
            question: "What are your strengths?",
            answer: "Relate to job role."
          },
          {
            question: "What are your weaknesses?",
            answer: "Show improvement."
          },
          {
            question: "Are you open to relocation?",
            answer: "Show flexibility."
          },
          {
            question: "Why should we hire you?",
            answer: "Match skills with role."
          }
        ]
      },
    
      {
        company: "Wipro",
        questions: [
          {
            question: "Tell me about yourself.",
            answer: "Brief intro with skills."
          },
          {
            question: "Why Wipro?",
            answer: "Talk about growth and opportunities."
          },
          {
            question: "Describe a team project.",
            answer: "Explain role and contribution."
          },
          {
            question: "Tell me about a challenge.",
            answer: "Explain problem-solving approach."
          },
          {
            question: "How do you handle stress?",
            answer: "Explain coping strategies."
          },
          {
            question: "Tell me about a failure.",
            answer: "Show learning."
          },
          {
            question: "What are your strengths?",
            answer: "Relate to job."
          },
          {
            question: "What are your weaknesses?",
            answer: "Show growth."
          },
          {
            question: "Where do you see yourself?",
            answer: "Show ambition."
          },
          {
            question: "Why should we hire you?",
            answer: "Align skills with company."
          }
        ]
      },
    
      {
        company: "Accenture",
        questions: [
          {
            question: "Tell me about yourself.",
            answer: "Highlight skills and education."
          },
          {
            question: "Why Accenture?",
            answer: "Talk about consulting and innovation."
          },
          {
            question: "Describe a challenging situation.",
            answer: "Explain how you handled it."
          },
          {
            question: "Tell me about teamwork.",
            answer: "Highlight collaboration."
          },
          {
            question: "Tell me about a failure.",
            answer: "Show learning."
          },
          {
            question: "How do you prioritize work?",
            answer: "Explain decision-making."
          },
          {
            question: "Tell me about leadership experience.",
            answer: "Show initiative."
          },
          {
            question: "How do you handle feedback?",
            answer: "Show improvement."
          },
          {
            question: "Where do you see yourself?",
            answer: "Show growth."
          },
          {
            question: "Why should we hire you?",
            answer: "Align skills with role."
          }
        ]
      }
  ];
  
  export default companyHRQuestions;