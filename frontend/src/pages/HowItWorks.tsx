import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  BookOpen, Bot, Scale, Cpu, Calculator, ChevronDown, ChevronRight,
  Shield, FileSearch, AlertTriangle, Lock, Users, Gavel, TrendingUp,
  Edit3, CheckCircle, ClipboardList, DollarSign, Clock, Zap, Server, Cloud, Code, Layers
} from 'lucide-react'

// Agent data
const AGENTS_DATA = [
  { name: 'Document Reviewer', codeName: 'document_reviewer', role: 'The Analyst', icon: FileSearch, color: 'text-blue-500', bgColor: 'bg-blue-500/10',
    description: 'First agent in the pipeline. Analyzes incoming documents to identify type, extract key information, and flag initial risk areas.',
    systemPrompt: 'You are a Document Review Agent specializing in financial document analysis. Your role is to identify the document type (marketing material, disclosure, agreement, etc.), summarize key content, extract claims and statements that may need compliance review, and flag initial risk areas for specialist agents.',
    rulesChecked: ['Document classification and categorization', 'Content extraction and summarization', 'Initial risk flagging', 'Metadata extraction'] },
  { name: 'FINRA Specialist', codeName: 'finra_specialist', role: 'The FINRA Expert', icon: Scale, color: 'text-purple-500', bgColor: 'bg-purple-500/10',
    description: 'Specializes in Financial Industry Regulatory Authority rules governing broker-dealers and investment communications.',
    systemPrompt: 'You are a FINRA Compliance Specialist. Analyze documents for violations of FINRA rules including communications standards, suitability requirements, and supervision obligations. Cite specific rule numbers and explain violations clearly.',
    rulesChecked: ['Rule 2210 - Communications with the Public', 'Rule 2111 - Suitability', 'Rule 3110 - Supervision', 'Rule 2010 - Standards of Commercial Honor', 'Rule 4512 - Customer Account Information'] },
  { name: 'SEC Specialist', codeName: 'sec_specialist', role: 'The SEC Expert', icon: Gavel, color: 'text-red-500', bgColor: 'bg-red-500/10',
    description: 'Focuses on Securities and Exchange Commission regulations for investment advisers and securities offerings.',
    systemPrompt: 'You are an SEC Compliance Specialist. Review documents for violations of SEC rules including investment company advertising, privacy requirements, best interest standards, and anti-fraud provisions. Provide specific rule citations.',
    rulesChecked: ['Rule 156 - Investment Company Sales Literature', 'Regulation S-P - Privacy of Consumer Financial Information', 'Regulation Best Interest (Reg BI)', 'Rule 10b-5 - Anti-Fraud Provisions', 'Form ADV Requirements'] },
  { name: 'CFPB Specialist', codeName: 'cfpb_specialist', role: 'The Consumer Advocate', icon: Users, color: 'text-green-500', bgColor: 'bg-green-500/10',
    description: 'Ensures compliance with Consumer Financial Protection Bureau regulations protecting consumers in financial transactions.',
    systemPrompt: 'You are a CFPB Compliance Specialist. Analyze documents for consumer protection violations including lending disclosures, fair credit practices, and unfair/deceptive practices. Focus on clear, consumer-friendly language requirements.',
    rulesChecked: ['TILA - Truth in Lending Act', 'RESPA - Real Estate Settlement Procedures Act', 'FCRA - Fair Credit Reporting Act', 'UDAAP - Unfair, Deceptive, or Abusive Acts or Practices', 'ECOA - Equal Credit Opportunity Act'] },
  { name: 'AML/KYC Agent', codeName: 'aml_kyc_agent', role: 'The Gatekeeper', icon: Shield, color: 'text-orange-500', bgColor: 'bg-orange-500/10',
    description: 'Monitors for anti-money laundering compliance and Know Your Customer requirements.',
    systemPrompt: 'You are an AML/KYC Compliance Agent. Review documents for compliance with anti-money laundering regulations, customer due diligence requirements, and suspicious activity reporting obligations. Flag potential red flags.',
    rulesChecked: ['Bank Secrecy Act (BSA)', 'USA PATRIOT Act', 'SAR - Suspicious Activity Report Requirements', 'CDD Rule - Customer Due Diligence', 'FinCEN Regulations'] },
  { name: 'Data Privacy Agent', codeName: 'data_privacy_agent', role: 'The Guardian', icon: Lock, color: 'text-cyan-500', bgColor: 'bg-cyan-500/10',
    description: 'Ensures data privacy compliance across multiple regulatory frameworks.',
    systemPrompt: 'You are a Data Privacy Compliance Agent. Analyze documents for privacy regulation compliance including data collection notices, consent requirements, and data handling practices. Consider both US and international privacy laws.',
    rulesChecked: ['GDPR - General Data Protection Regulation', 'CCPA - California Consumer Privacy Act', 'HIPAA - Health Insurance Portability and Accountability Act', 'GLBA Privacy Rule - Gramm-Leach-Bliley Act', 'State Privacy Laws'] },
  { name: 'Regulatory Expert', codeName: 'regulatory_expert', role: 'The Coordinator', icon: Layers, color: 'text-indigo-500', bgColor: 'bg-indigo-500/10',
    description: 'Aggregates findings from all specialist agents, removes duplicates, and prioritizes by severity.',
    systemPrompt: 'You are a Senior Regulatory Expert. Review and consolidate findings from all specialist agents. Remove duplicate violations, resolve conflicting assessments, rank issues by severity and business impact, and provide a unified compliance assessment.',
    rulesChecked: ['Cross-regulation conflict resolution', 'Severity prioritization', 'Duplicate detection and merging', 'Comprehensive risk assessment'] },
  { name: 'Risk Assessment', codeName: 'risk_assessment', role: 'The Scorer', icon: TrendingUp, color: 'text-yellow-500', bgColor: 'bg-yellow-500/10',
    description: 'Calculates compliance and risk scores based on violation severity and count.',
    systemPrompt: 'You are a Risk Assessment Agent. Calculate compliance scores (0-100) and risk levels based on violation severity. Use weighted scoring: Critical (-30), High (-15), Medium (-5), Low (-2). Assign letter grades and risk categories.',
    rulesChecked: ['Weighted severity scoring', 'Compliance score calculation (0-100)', 'Risk level categorization', 'Letter grade assignment (A-F)'] },
  { name: 'Legal Writer', codeName: 'legal_writer', role: 'The Editor', icon: Edit3, color: 'text-pink-500', bgColor: 'bg-pink-500/10',
    description: 'Generates compliant alternative text for identified violations.',
    systemPrompt: 'You are a Legal Writing Specialist. For each violation identified, generate compliant alternative language that maintains the original intent while meeting regulatory requirements. Provide clear before/after comparisons.',
    rulesChecked: ['Compliant language generation', 'Tone and clarity optimization', 'Regulatory requirement alignment', 'Plain language standards'] },
  { name: 'Citation Validator', codeName: 'citation_validator', role: 'The Fact-Checker', icon: CheckCircle, color: 'text-emerald-500', bgColor: 'bg-emerald-500/10',
    description: 'Validates that all regulatory citations are accurate and current.',
    systemPrompt: 'You are a Citation Validation Agent. Verify all regulatory citations referenced in the compliance review are accurate, current, and properly formatted. Flag any outdated or incorrect rule references.',
    rulesChecked: ['Citation accuracy verification', 'Rule currency validation', 'Proper citation formatting', 'Cross-reference checking'] },
  { name: 'Quality Assurance', codeName: 'quality_assurance', role: 'The Validator', icon: ClipboardList, color: 'text-teal-500', bgColor: 'bg-teal-500/10',
    description: 'Final quality check to validate findings and identify false positives.',
    systemPrompt: 'You are a Quality Assurance Agent. Perform final validation of all compliance findings. Check for false positives, verify severity assignments are appropriate, ensure all violations have proper citations and corrections, and validate overall review quality.',
    rulesChecked: ['False positive detection', 'Severity validation', 'Completeness checking', 'Review quality scoring'] },
  { name: 'Audit Trail', codeName: 'audit_trail', role: 'The Scribe', icon: BookOpen, color: 'text-slate-500', bgColor: 'bg-slate-500/10',
    description: 'Documents the complete review process for regulatory audit purposes.',
    systemPrompt: 'You are an Audit Trail Agent. Document the complete compliance review process including all agent actions, findings, decisions, and timestamps. Generate a comprehensive audit log suitable for regulatory examination.',
    rulesChecked: ['Process documentation', 'Decision logging', 'Timestamp recording', 'Audit-ready reporting'] }
]

// Compliance rules
const COMPLIANCE_RULES: Record<string, { name: string; description: string; color: string; bgColor: string; rules: { code: string; name: string; description: string; keyRequirements: string[] }[] }> = {
  FINRA: { name: 'Financial Industry Regulatory Authority', description: 'Self-regulatory organization overseeing broker-dealers and registered representatives.', color: 'text-purple-500', bgColor: 'bg-purple-500/10',
    rules: [
      { code: 'Rule 2210', name: 'Communications with the Public', description: 'Governs all broker-dealer communications including advertisements, sales literature, and correspondence.', keyRequirements: ['Must be based on principles of fair dealing', 'Cannot omit material facts', 'Must include balanced presentation of risks and benefits', 'Performance data must include standardized disclosures'] },
      { code: 'Rule 2111', name: 'Suitability', description: 'Requires broker-dealers to have a reasonable basis to believe recommendations are suitable for customers.', keyRequirements: ['Reasonable-basis suitability', 'Customer-specific suitability', 'Quantitative suitability', 'Must document suitability analysis'] },
      { code: 'Rule 3110', name: 'Supervision', description: 'Requires firms to establish and maintain supervisory systems and written procedures.', keyRequirements: ['Written supervisory procedures required', 'Designated supervisory principals', 'Regular compliance reviews', 'Documentation of supervisory activities'] },
      { code: 'Rule 2010', name: 'Standards of Commercial Honor', description: 'Requires members to observe high standards of commercial honor and just principles of trade.', keyRequirements: ['Ethical conduct in all business dealings', 'No manipulation or deception', 'Fair treatment of customers', 'Professional business standards'] },
      { code: 'Rule 4512', name: 'Customer Account Information', description: 'Requires maintenance of accurate customer account records.', keyRequirements: ['Collect and maintain customer information', 'Update records periodically', 'Document investment objectives', 'Record risk tolerance'] }
    ] },
  SEC: { name: 'Securities and Exchange Commission', description: 'Federal agency responsible for enforcing securities laws.', color: 'text-red-500', bgColor: 'bg-red-500/10',
    rules: [
      { code: 'Rule 156', name: 'Investment Company Sales Literature', description: 'Prohibits materially misleading statements in investment company sales literature.', keyRequirements: ['No misleading statements about fund performance', 'Must present risks prominently', 'Cannot guarantee future results', 'Past performance disclaimers required'] },
      { code: 'Regulation S-P', name: 'Privacy of Consumer Financial Information', description: 'Requires financial institutions to protect consumer financial information.', keyRequirements: ['Initial and annual privacy notices', 'Opt-out rights for information sharing', 'Safeguards for customer information', 'Proper disposal of consumer information'] },
      { code: 'Regulation BI', name: 'Regulation Best Interest', description: 'Establishes a "best interest" standard for broker-dealers.', keyRequirements: ['Disclosure of material facts about relationship', 'Exercise reasonable diligence and care', 'Identify and mitigate conflicts of interest', 'Establish policies to achieve compliance'] },
      { code: 'Rule 10b-5', name: 'Anti-Fraud Provisions', description: 'Prohibits fraud and deceit in connection with securities transactions.', keyRequirements: ['No false statements of material fact', 'No omission of material facts', 'No fraudulent schemes or devices', 'Applies to all securities transactions'] },
      { code: 'Form ADV', name: 'Investment Adviser Registration', description: 'Required disclosure document for registered investment advisers.', keyRequirements: ['Disclose advisory services and fees', 'Describe conflicts of interest', 'Provide disciplinary history', 'Deliver to clients annually'] }
    ] },
  CFPB: { name: 'Consumer Financial Protection Bureau', description: 'Federal agency focused on consumer protection in the financial sector.', color: 'text-green-500', bgColor: 'bg-green-500/10',
    rules: [
      { code: 'TILA', name: 'Truth in Lending Act', description: 'Requires clear disclosure of loan terms and costs.', keyRequirements: ['Disclose APR and finance charges', 'Provide loan cost estimates', 'Right of rescission for certain loans', 'Standardized disclosure formats'] },
      { code: 'RESPA', name: 'Real Estate Settlement Procedures Act', description: 'Requires disclosures in real estate transactions.', keyRequirements: ['Good Faith Estimate of settlement costs', 'HUD-1 Settlement Statement', 'No kickbacks or referral fees', 'Mortgage servicing transfer notices'] },
      { code: 'FCRA', name: 'Fair Credit Reporting Act', description: 'Regulates collection and use of consumer credit information.', keyRequirements: ['Accuracy of credit reports', 'Consumer access to credit reports', 'Dispute resolution procedures', 'Permissible purposes for credit checks'] },
      { code: 'UDAAP', name: 'Unfair, Deceptive, or Abusive Acts', description: 'Prohibits unfair, deceptive, or abusive practices.', keyRequirements: ['No unfair practices causing substantial injury', 'No deceptive acts or omissions', 'No abusive practices exploiting consumers', 'Clear and prominent disclosures'] },
      { code: 'ECOA', name: 'Equal Credit Opportunity Act', description: 'Prohibits discrimination in credit transactions.', keyRequirements: ['No discrimination based on protected classes', 'Adverse action notices required', 'Record retention requirements', 'Fair lending analysis'] }
    ] },
  AML: { name: 'Anti-Money Laundering', description: 'Regulations designed to prevent money laundering and terrorist financing.', color: 'text-orange-500', bgColor: 'bg-orange-500/10',
    rules: [
      { code: 'BSA', name: 'Bank Secrecy Act', description: 'Requires financial institutions to assist in detecting and preventing money laundering.', keyRequirements: ['Currency Transaction Reports (CTRs)', 'Suspicious Activity Reports (SARs)', 'Record keeping requirements', 'AML compliance program'] },
      { code: 'PATRIOT Act', name: 'USA PATRIOT Act', description: 'Expanded BSA requirements and enhanced customer identification.', keyRequirements: ['Customer Identification Program (CIP)', 'Enhanced due diligence for high-risk accounts', 'Information sharing with government', 'Correspondent banking restrictions'] },
      { code: 'CDD Rule', name: 'Customer Due Diligence Rule', description: 'Requires identification and verification of beneficial owners.', keyRequirements: ['Identify beneficial owners (25%+ ownership)', 'Verify customer identity', 'Understand nature of customer relationship', 'Ongoing monitoring'] },
      { code: 'SAR', name: 'Suspicious Activity Reporting', description: 'Requires reporting of suspicious transactions.', keyRequirements: ['Report suspicious transactions over $5,000', 'File within 30 days of detection', 'Maintain confidentiality', 'No tipping off customers'] },
      { code: 'FinCEN', name: 'FinCEN Regulations', description: 'Treasury bureau that administers BSA.', keyRequirements: ['Register with FinCEN as required', 'File required reports electronically', 'Respond to information requests', 'Maintain compliance with guidance'] }
    ] },
  Privacy: { name: 'Data Privacy Regulations', description: 'Laws protecting consumer personal and financial data.', color: 'text-cyan-500', bgColor: 'bg-cyan-500/10',
    rules: [
      { code: 'GDPR', name: 'General Data Protection Regulation', description: 'EU regulation on data protection and privacy.', keyRequirements: ['Lawful basis for processing', 'Data subject rights (access, deletion, portability)', 'Data breach notification (72 hours)', 'Privacy by design and default'] },
      { code: 'CCPA', name: 'California Consumer Privacy Act', description: 'California law granting consumers rights over their personal information.', keyRequirements: ['Right to know what data is collected', 'Right to delete personal information', 'Right to opt-out of data sale', 'Non-discrimination for exercising rights'] },
      { code: 'HIPAA', name: 'Health Insurance Portability Act', description: 'Protects sensitive patient health information.', keyRequirements: ['Privacy Rule compliance', 'Security Rule safeguards', 'Breach notification requirements', 'Business Associate Agreements'] },
      { code: 'GLBA', name: 'Gramm-Leach-Bliley Act', description: 'Requires financial institutions to explain information-sharing practices.', keyRequirements: ['Privacy notices to consumers', 'Safeguards Rule implementation', 'Pretexting protection', 'Opt-out provisions'] },
      { code: 'State Laws', name: 'State Privacy Laws', description: 'Various state-level privacy regulations.', keyRequirements: ['Consumer rights similar to CCPA', 'Data protection assessments', 'Consent requirements vary by state', 'Enforcement and penalties differ'] }
    ] }
}

// Tech stack
const TECH_STACK = {
  frontend: { title: 'Frontend', icon: Code, color: 'text-blue-500',
    technologies: [
      { name: 'React', version: '18.2.0', description: 'Component-based UI library' },
      { name: 'TypeScript', version: '5.3.3', description: 'Type-safe JavaScript' },
      { name: 'Vite', version: '5.0.12', description: 'Next-gen build tool' },
      { name: 'TailwindCSS', version: '3.4.1', description: 'Utility-first CSS framework' },
      { name: 'Redux Toolkit', version: '2.0.1', description: 'State management' },
      { name: 'Framer Motion', version: '10.18.0', description: 'Animation library' }
    ] },
  backend: { title: 'Backend', icon: Server, color: 'text-green-500',
    technologies: [
      { name: 'FastAPI', version: '0.109.0', description: 'Modern Python web framework' },
      { name: 'SQLAlchemy', version: '2.0.25', description: 'SQL toolkit and ORM' },
      { name: 'LangChain', version: '0.1.4', description: 'LLM application framework' },
      { name: 'LangGraph', version: '0.0.24', description: 'Agent orchestration' },
      { name: 'Pydantic', version: '2.5.3', description: 'Data validation' },
      { name: 'WebSockets', version: '12.0', description: 'Real-time communication' }
    ] },
  infrastructure: { title: 'Infrastructure', icon: Cloud, color: 'text-purple-500',
    technologies: [
      { name: 'PostgreSQL', version: '15+', description: 'Primary database' },
      { name: 'Redis', version: '5.0.1', description: 'Caching layer' },
      { name: 'AWS Bedrock', version: 'Nova Pro', description: 'AI/LLM inference' },
      { name: 'AWS S3', version: '-', description: 'Document storage' },
      { name: 'AWS Textract', version: '-', description: 'Document OCR' }
    ] },
  ai: { title: 'AI & ML', icon: Bot, color: 'text-orange-500',
    technologies: [
      { name: 'Amazon Nova Pro', version: 'v1:0', description: 'Primary LLM model' },
      { name: 'Multi-Agent System', version: '12 agents', description: 'Specialized compliance agents' },
      { name: 'LangGraph Workflow', version: '-', description: 'Agent orchestration' }
    ] }
}

// ROI data
const ROI_DATA = {
  manual: { avgSalary: 105000, hoursPerDocument: 3, errorRate: 0.15, avgFinePerError: 50000 },
  automated: { costPerDocument: 2.50, minutesPerDocument: 3, errorRate: 0.03, setupCost: 25000, monthlyMaintenance: 500 }
}

export default function HowItWorks() {
  const [activeSection, setActiveSection] = useState<string>('agents')
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null)
  const [expandedRegulator, setExpandedRegulator] = useState<string | null>('FINRA')
  const [expandedRule, setExpandedRule] = useState<string | null>(null)
  const [documentsPerYear, setDocumentsPerYear] = useState(500)
  const [complianceOfficers, setComplianceOfficers] = useState(2)

  // ROI Calculations
  const calculateROI = () => {
    const manual = ROI_DATA.manual
    const auto = ROI_DATA.automated
    const manualLaborCost = complianceOfficers * manual.avgSalary
    const manualHoursTotal = documentsPerYear * manual.hoursPerDocument
    const manualErrorCost = documentsPerYear * manual.errorRate * manual.avgFinePerError * 0.1
    const totalManualCost = manualLaborCost + manualErrorCost
    const autoCostPerYear = (documentsPerYear * auto.costPerDocument) + (auto.monthlyMaintenance * 12)
    const autoErrorCost = documentsPerYear * auto.errorRate * manual.avgFinePerError * 0.1
    const totalAutoCostFirstYear = auto.setupCost + autoCostPerYear + autoErrorCost
    const totalAutoCostOngoing = autoCostPerYear + autoErrorCost
    const ongoingSavings = totalManualCost - totalAutoCostOngoing
    const roiPercent = ((ongoingSavings / totalAutoCostOngoing) * 100).toFixed(0)
    return { manualLaborCost, manualHoursTotal, manualErrorCost, totalManualCost, autoCostPerYear, autoErrorCost, totalAutoCostFirstYear, totalAutoCostOngoing, ongoingSavings, roiPercent }
  }

  const roi = calculateROI()
  const sections = [
    { id: 'agents', label: 'AI Agents', icon: Bot },
    { id: 'rules', label: 'Compliance Rules', icon: Scale },
    { id: 'tech', label: 'Tech Stack', icon: Cpu },
    { id: 'roi', label: 'ROI Calculator', icon: Calculator },
  ]

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-heading font-bold text-secondary-900 flex items-center gap-3">
          <BookOpen className="h-8 w-8 text-primary-600" />
          How It Works
        </h1>
        <p className="text-secondary-600 mt-1">Explore our AI-powered compliance review system</p>
      </motion.div>

      {/* Section Tabs */}
      <div className="flex flex-wrap gap-2">
        {sections.map((section) => (
          <button key={section.id} onClick={() => setActiveSection(section.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${activeSection === section.id ? 'bg-primary-600 text-white' : 'bg-white hover:bg-secondary-50 border border-secondary-200'}`}>
            <section.icon className="h-4 w-4" />
            {section.label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {/* Agents Section */}
        {activeSection === 'agents' && (
          <motion.div key="agents" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-4">
            <div className="card">
              <div className="p-6 border-b border-secondary-200">
                <h2 className="text-lg font-heading font-semibold text-secondary-900 flex items-center gap-2">
                  <Bot className="h-5 w-5 text-primary-600" />
                  12-Agent Compliance Pipeline
                </h2>
                <p className="text-sm text-secondary-600 mt-1">Our multi-agent system uses specialized AI agents that work together to provide comprehensive compliance review.</p>
              </div>
              <div className="p-6 space-y-3">
                {AGENTS_DATA.map((agent, index) => (
                  <motion.div key={agent.codeName} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.05 }} className="border border-secondary-200 rounded-lg overflow-hidden">
                    <button onClick={() => setExpandedAgent(expandedAgent === agent.codeName ? null : agent.codeName)} className="w-full flex items-center justify-between p-4 hover:bg-secondary-50 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${agent.bgColor}`}><agent.icon className={`h-5 w-5 ${agent.color}`} /></div>
                        <div className="text-left">
                          <div className="font-medium">{agent.name}</div>
                          <div className="text-sm text-secondary-500">{agent.role}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs bg-secondary-100 px-2 py-1 rounded">Agent {index + 1}</span>
                        {expandedAgent === agent.codeName ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </div>
                    </button>
                    <AnimatePresence>
                      {expandedAgent === agent.codeName && (
                        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="border-t border-secondary-200 bg-secondary-50">
                          <div className="p-4 space-y-4">
                            <p className="text-sm">{agent.description}</p>
                            <div>
                              <h4 className="text-sm font-medium mb-2">System Prompt</h4>
                              <div className="bg-white p-3 rounded-lg text-sm text-secondary-600 font-mono border border-secondary-200">{agent.systemPrompt}</div>
                            </div>
                            <div>
                              <h4 className="text-sm font-medium mb-2">Rules & Functions</h4>
                              <ul className="space-y-1">
                                {agent.rulesChecked.map((rule, i) => (
                                  <li key={i} className="flex items-center gap-2 text-sm"><CheckCircle className="h-3 w-3 text-green-500" />{rule}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Rules Section */}
        {activeSection === 'rules' && (
          <motion.div key="rules" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-4">
            <div className="card">
              <div className="p-6 border-b border-secondary-200">
                <h2 className="text-lg font-heading font-semibold text-secondary-900 flex items-center gap-2">
                  <Scale className="h-5 w-5 text-primary-600" />
                  Compliance Rules by Regulatory Body
                </h2>
                <p className="text-sm text-secondary-600 mt-1">Comprehensive coverage of financial regulations.</p>
              </div>
              <div className="p-6">
                <div className="flex flex-wrap gap-2 mb-4">
                  {Object.entries(COMPLIANCE_RULES).map(([key, regulator]) => (
                    <button key={key} onClick={() => { setExpandedRegulator(key); setExpandedRule(null) }}
                      className={`px-3 py-1.5 rounded-lg text-sm transition-all ${expandedRegulator === key ? `${regulator.bgColor} ${regulator.color} font-medium` : 'bg-secondary-100 hover:bg-secondary-200'}`}>
                      {key}
                    </button>
                  ))}
                </div>
                {expandedRegulator && (
                  <motion.div key={expandedRegulator} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                    <div className={`p-4 rounded-lg ${COMPLIANCE_RULES[expandedRegulator].bgColor}`}>
                      <h3 className={`font-semibold ${COMPLIANCE_RULES[expandedRegulator].color}`}>{COMPLIANCE_RULES[expandedRegulator].name}</h3>
                      <p className="text-sm mt-1 text-secondary-600">{COMPLIANCE_RULES[expandedRegulator].description}</p>
                    </div>
                    <div className="space-y-2">
                      {COMPLIANCE_RULES[expandedRegulator].rules.map((rule) => (
                        <div key={rule.code} className="border border-secondary-200 rounded-lg overflow-hidden">
                          <button onClick={() => setExpandedRule(expandedRule === rule.code ? null : rule.code)} className="w-full flex items-center justify-between p-3 hover:bg-secondary-50 transition-colors">
                            <div className="flex items-center gap-3">
                              <span className={`text-sm font-mono px-2 py-0.5 rounded ${COMPLIANCE_RULES[expandedRegulator].bgColor} ${COMPLIANCE_RULES[expandedRegulator].color}`}>{rule.code}</span>
                              <span className="font-medium text-sm">{rule.name}</span>
                            </div>
                            {expandedRule === rule.code ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                          </button>
                          <AnimatePresence>
                            {expandedRule === rule.code && (
                              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="border-t border-secondary-200 bg-secondary-50">
                                <div className="p-4 space-y-3">
                                  <p className="text-sm">{rule.description}</p>
                                  <div>
                                    <h4 className="text-sm font-medium mb-2">Key Requirements</h4>
                                    <ul className="space-y-1">
                                      {rule.keyRequirements.map((req, i) => (
                                        <li key={i} className="flex items-start gap-2 text-sm"><AlertTriangle className="h-3 w-3 text-yellow-500 mt-1 flex-shrink-0" />{req}</li>
                                      ))}
                                    </ul>
                                  </div>
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* Tech Stack Section */}
        {activeSection === 'tech' && (
          <motion.div key="tech" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(TECH_STACK).map(([key, category], index) => (
              <motion.div key={key} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.1 }} className="card">
                <div className="p-4 border-b border-secondary-200">
                  <h2 className={`text-lg font-semibold flex items-center gap-2 ${category.color}`}>
                    <category.icon className="h-5 w-5" />
                    {category.title}
                  </h2>
                </div>
                <div className="p-4 space-y-2">
                  {category.technologies.map((tech) => (
                    <div key={tech.name} className="flex items-center justify-between p-2 rounded-lg bg-secondary-50 hover:bg-secondary-100 transition-colors">
                      <div>
                        <span className="font-medium text-sm">{tech.name}</span>
                        <p className="text-xs text-secondary-500">{tech.description}</p>
                      </div>
                      <span className="text-xs font-mono bg-white px-2 py-1 rounded border border-secondary-200">{tech.version}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}

        {/* ROI Calculator Section */}
        {activeSection === 'roi' && (
          <motion.div key="roi" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-4">
            {/* Input Parameters */}
            <div className="card">
              <div className="p-6 border-b border-secondary-200">
                <h2 className="text-lg font-heading font-semibold text-secondary-900 flex items-center gap-2">
                  <Calculator className="h-5 w-5 text-primary-600" />
                  ROI Calculator
                </h2>
                <p className="text-sm text-secondary-600 mt-1">Compare manual compliance review vs. AI-powered automation. Based on 2026 US industry averages.</p>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2">Documents Reviewed Per Year</label>
                    <input type="range" min="100" max="5000" step="100" value={documentsPerYear} onChange={(e) => setDocumentsPerYear(parseInt(e.target.value))} className="w-full" />
                    <div className="flex justify-between text-sm text-secondary-500 mt-1">
                      <span>100</span>
                      <span className="font-medium text-secondary-900">{documentsPerYear.toLocaleString()}</span>
                      <span>5,000</span>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Current Compliance Officers</label>
                    <input type="range" min="1" max="10" value={complianceOfficers} onChange={(e) => setComplianceOfficers(parseInt(e.target.value))} className="w-full" />
                    <div className="flex justify-between text-sm text-secondary-500 mt-1">
                      <span>1</span>
                      <span className="font-medium text-secondary-900">{complianceOfficers}</span>
                      <span>10</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Manual Review */}
              <div className="card border-red-200">
                <div className="p-4 border-b border-secondary-200">
                  <h2 className="text-lg font-semibold text-red-600 flex items-center gap-2"><Users className="h-5 w-5" />Manual Review</h2>
                </div>
                <div className="p-4 space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm"><span className="text-secondary-500">Labor Cost ({complianceOfficers} officers × $105K)</span><span className="font-medium">${roi.manualLaborCost.toLocaleString()}</span></div>
                    <div className="flex justify-between text-sm"><span className="text-secondary-500">Hours Per Year ({documentsPerYear} × 3 hrs)</span><span className="font-medium">{roi.manualHoursTotal.toLocaleString()} hrs</span></div>
                    <div className="flex justify-between text-sm"><span className="text-secondary-500">Error Rate</span><span className="font-medium text-red-500">15%</span></div>
                    <div className="flex justify-between text-sm"><span className="text-secondary-500">Estimated Error-Related Risk</span><span className="font-medium">${roi.manualErrorCost.toLocaleString()}</span></div>
                  </div>
                  <div className="border-t pt-3">
                    <div className="flex justify-between"><span className="font-semibold">Total Annual Cost</span><span className="font-bold text-red-600 text-xl">${roi.totalManualCost.toLocaleString()}</span></div>
                  </div>
                </div>
              </div>

              {/* Automated Review */}
              <div className="card border-green-200">
                <div className="p-4 border-b border-secondary-200">
                  <h2 className="text-lg font-semibold text-green-600 flex items-center gap-2"><Zap className="h-5 w-5" />AI-Powered Review</h2>
                </div>
                <div className="p-4 space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm"><span className="text-secondary-500">Processing Cost ({documentsPerYear} × $2.50)</span><span className="font-medium">${(documentsPerYear * 2.5).toLocaleString()}</span></div>
                    <div className="flex justify-between text-sm"><span className="text-secondary-500">Monthly Maintenance (× 12)</span><span className="font-medium">${(500 * 12).toLocaleString()}</span></div>
                    <div className="flex justify-between text-sm"><span className="text-secondary-500">Error Rate</span><span className="font-medium text-green-500">3%</span></div>
                    <div className="flex justify-between text-sm"><span className="text-secondary-500">Estimated Error-Related Risk</span><span className="font-medium">${roi.autoErrorCost.toLocaleString()}</span></div>
                    <div className="flex justify-between text-sm"><span className="text-secondary-500">One-Time Setup (Year 1 only)</span><span className="font-medium">${ROI_DATA.automated.setupCost.toLocaleString()}</span></div>
                  </div>
                  <div className="border-t pt-3">
                    <div className="flex justify-between"><span className="font-semibold">Annual Cost (Ongoing)</span><span className="font-bold text-green-600 text-xl">${roi.totalAutoCostOngoing.toLocaleString()}</span></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Savings Summary */}
            <div className="card bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
              <div className="p-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-2 mb-1"><DollarSign className="h-5 w-5 text-green-500" /><span className="text-sm text-secondary-600">Annual Savings</span></div>
                    <p className="text-2xl font-bold text-green-600">${roi.ongoingSavings.toLocaleString()}</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-2 mb-1"><Clock className="h-5 w-5 text-blue-500" /><span className="text-sm text-secondary-600">Hours Saved</span></div>
                    <p className="text-2xl font-bold text-blue-600">{roi.manualHoursTotal.toLocaleString()}</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-2 mb-1"><TrendingUp className="h-5 w-5 text-purple-500" /><span className="text-sm text-secondary-600">ROI</span></div>
                    <p className="text-2xl font-bold text-purple-600">{roi.roiPercent}%</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-2 mb-1"><Shield className="h-5 w-5 text-orange-500" /><span className="text-sm text-secondary-600">Error Reduction</span></div>
                    <p className="text-2xl font-bold text-orange-600">80%</p>
                  </div>
                </div>
                <div className="mt-6 p-4 bg-white rounded-lg border border-secondary-200">
                  <h4 className="font-semibold mb-2">Industry Benchmarks (2026)</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div><span className="text-secondary-500">Avg Compliance Officer Salary</span><p className="font-medium">$105,000/year</p></div>
                    <div><span className="text-secondary-500">Manual Review Time</span><p className="font-medium">2-4 hours/document</p></div>
                    <div><span className="text-secondary-500">Manual Error Rate</span><p className="font-medium">10-20%</p></div>
                    <div><span className="text-secondary-500">Avg Regulatory Fine</span><p className="font-medium">$50,000+</p></div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
